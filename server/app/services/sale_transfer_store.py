from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.services.sale_transfer_audit import write_sale_audit


# -----------------------------------------------------------------------------
# Engine handling (fix: always use same DB file via LTC_DB_PATH)
# -----------------------------------------------------------------------------

_ENGINE_CACHE: Dict[str, Engine] = {}


def _sqlite_url_from_path(path: str) -> str:
    p = (path or "").strip()
    if not p:
        raise RuntimeError("LTC_DB_PATH fehlt")
    # Windows: sqlite:///C:/path/file.db
    p = p.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", p):
        return f"sqlite:///{p}"
    if p.startswith("/"):
        return f"sqlite:////{p.lstrip('/')}"
    return f"sqlite:///{p}"


def _get_engine_for_sale_transfer(db: Session) -> Engine:
    """
    Prefer LTC_DB_PATH (tests setzen das). Fallback: Session bind.
    Cache keyed by URL to survive multiple requests.
    """
    env_path = (os.getenv("LTC_DB_PATH") or "").strip()
    if env_path:
        url = _sqlite_url_from_path(env_path)
        eng = _ENGINE_CACHE.get(url)
        if eng is None:
            eng = create_engine(url, connect_args={"check_same_thread": False})
            _ENGINE_CACHE[url] = eng
        return eng

    bind = db.get_bind()
    if isinstance(bind, Engine):
        return bind
    if isinstance(bind, Connection):
        return bind.engine
    raise RuntimeError("DB bind ist weder Engine noch Connection (und LTC_DB_PATH fehlt)")


# -----------------------------------------------------------------------------
# Time helpers (UTC, tz-naiv for SQLite friendliness)
# -----------------------------------------------------------------------------

def _utc_now() -> datetime:
    # UTC, tz-naiv, seconds precision
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _iso_z(dt: datetime) -> str:
    # output as Z
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# -----------------------------------------------------------------------------
# Crypto / Config
# -----------------------------------------------------------------------------

def _get_secret_key() -> str:
    secret = (os.getenv("LTC_SECRET_KEY") or "").strip()
    if len(secret) < 16:
        raise RuntimeError("LTC_SECRET_KEY fehlt/zu kurz (>=16)")
    return secret


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


# -----------------------------------------------------------------------------
# DB Table: sale_transfers
# -----------------------------------------------------------------------------

def _ensure_sale_transfer_table(engine: Engine) -> Table:
    insp = sa_inspect(engine)
    md = MetaData()
    name = "sale_transfers"

    if insp.has_table(name):
        return Table(name, md, autoload_with=engine)

    t = Table(
        name,
        md,
        Column("transfer_id", String(36), primary_key=True),
        Column("token_hmac", String(64), nullable=False, unique=True, index=True),
        Column("vehicle_id", String(128), nullable=False, index=True),
        Column("status", String(16), nullable=False, index=True),  # created|redeemed|cancelled|expired
        Column("created_at", DateTime(timezone=False), nullable=False, index=True),
        Column("expires_at", DateTime(timezone=False), nullable=False, index=True),
        Column("initiator_user_id", String(36), nullable=False, index=True),
        Column("initiator_role", String(16), nullable=False),
        Column("redeemed_by_user_id", String(36), nullable=True, index=True),
        Column("redeemed_by_role", String(16), nullable=True),
        Column("redeemed_at", DateTime(timezone=False), nullable=True),
        Column("cancelled_at", DateTime(timezone=False), nullable=True),
        Column("expired_at", DateTime(timezone=False), nullable=True),
        Column("ownership_transferred", Boolean, nullable=False, server_default=text("0")),
    )

    md.create_all(bind=engine)
    return t


def _row_by_token_hmac(engine: Engine, t: Table, token_h: str) -> Optional[Dict[str, Any]]:
    with engine.connect() as conn:
        r = conn.execute(select(t).where(t.c.token_hmac == token_h).limit(1)).mappings().first()
        return dict(r) if r else None


def _row_by_transfer_id(engine: Engine, t: Table, transfer_id: str) -> Optional[Dict[str, Any]]:
    with engine.connect() as conn:
        r = conn.execute(select(t).where(t.c.transfer_id == transfer_id).limit(1)).mappings().first()
        return dict(r) if r else None


def _maybe_mark_expired(engine: Engine, t: Table, row: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    exp = row.get("expires_at")
    if row.get("status") == "created" and isinstance(exp, datetime):
        if _naive_utc(exp) <= _naive_utc(now):
            with engine.begin() as conn:
                conn.execute(
                    update(t)
                    .where(t.c.transfer_id == row["transfer_id"])
                    .values(status="expired", expired_at=_naive_utc(now))
                )
            row["status"] = "expired"
            row["expired_at"] = _naive_utc(now)
    return row


# -----------------------------------------------------------------------------
# Ownership transfer best-effort (uses SAME engine)
# -----------------------------------------------------------------------------

_OWNER_COL_CANDIDATES = ("owner_id", "user_id", "account_id", "created_by_user_id", "created_by")


def _try_transfer_ownership_best_effort(engine: Engine, vehicle_id: str, new_owner_user_id: str) -> bool:
    insp = sa_inspect(engine)
    names = insp.get_table_names()

    cand = [n for n in names if re.search(r"(vehicle|vehicles|servicebook|servicebooks|fahrzeug)", n, re.IGNORECASE)]
    md = MetaData()

    with engine.begin() as conn:
        for table_name in cand:
            try:
                vt = Table(table_name, md, autoload_with=engine)
            except Exception:
                continue

            if "id" not in vt.c:
                continue

            owner_key = None
            for c in _OWNER_COL_CANDIDATES:
                if c in vt.c:
                    owner_key = c
                    break
            if not owner_key:
                continue

            try:
                res = conn.execute(
                    update(vt)
                    .where(vt.c.id == vehicle_id)
                    .values({owner_key: new_owner_user_id})
                )
                if getattr(res, "rowcount", 0) and res.rowcount > 0:
                    return True
            except Exception:
                continue

    return False


# -----------------------------------------------------------------------------
# Public service functions (signatures unchanged)
# -----------------------------------------------------------------------------

def create_transfer(
    *,
    db: Session,
    initiator_user_id: str,
    initiator_role: str,
    vehicle_id: str,
    ttl_seconds: Optional[int],
) -> Dict[str, Any]:
    if initiator_role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    engine = _get_engine_for_sale_transfer(db)
    t = _ensure_sale_transfer_table(engine)
    secret = _get_secret_key()

    ttl = int(ttl_seconds or 900)
    if ttl < 60 or ttl > 7 * 24 * 3600:
        raise HTTPException(status_code=400, detail="ttl_seconds_out_of_range")

    now = _utc_now()
    expires = now + timedelta(seconds=ttl)

    transfer_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    token_h = _hmac_hex(secret, token)

    payload = {
        "transfer_id": transfer_id,
        "vehicle_id_hmac": _hmac_hex(secret, vehicle_id),
        "expires_at": _iso_z(expires.replace(tzinfo=timezone.utc)),
    }

    with engine.begin() as conn:
        conn.execute(
            insert(t).values(
                transfer_id=transfer_id,
                token_hmac=token_h,
                vehicle_id=vehicle_id,
                status="created",
                created_at=now,
                expires_at=expires,
                initiator_user_id=initiator_user_id,
                initiator_role=initiator_role,
                ownership_transferred=False,
            )
        )

    # Audit best-effort (darf business nicht killen)
    try:
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_CREATED",
            actor_user_id=initiator_user_id,
            target_id=transfer_id,
            payload=payload,
        )
    except Exception:
        pass

    return {
        "transfer_id": transfer_id,
        "transfer_token": token,
        "expires_at": _iso_z(expires.replace(tzinfo=timezone.utc)),
        "status": "created",
    }


def redeem_transfer(
    *,
    db: Session,
    redeemer_user_id: str,
    redeemer_role: str,
    transfer_token: str,
) -> Dict[str, Any]:
    if redeemer_role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    engine = _get_engine_for_sale_transfer(db)
    t = _ensure_sale_transfer_table(engine)
    secret = _get_secret_key()
    now = _utc_now()

    token_h = _hmac_hex(secret, transfer_token)
    row = _row_by_token_hmac(engine, t, token_h)

    if not row:
        try:
            write_sale_audit(
                db,
                event_type="SALE_TRANSFER_REDEEM_FAILED",
                actor_user_id=redeemer_user_id,
                target_id="unknown",
                payload={"reason": "not_found"},
            )
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="transfer_not_found")

    row = _maybe_mark_expired(engine, t, row, now)

    if row.get("status") == "expired":
        raise HTTPException(status_code=410, detail="transfer_expired")

    if row.get("status") != "created":
        # zweites Redeem => 409 (Test akzeptiert 409/410)
        raise HTTPException(status_code=409, detail="transfer_not_redeemable")

    # Atomarer Claim: nur 1x redeembar
    with engine.begin() as conn:
        res = conn.execute(
            update(t)
            .where(t.c.transfer_id == row["transfer_id"])
            .where(t.c.status == "created")
            .values(
                status="redeemed",
                redeemed_by_user_id=redeemer_user_id,
                redeemed_by_role=redeemer_role,
                redeemed_at=now,
                ownership_transferred=False,
            )
        )
        if getattr(res, "rowcount", 0) != 1:
            raise HTTPException(status_code=409, detail="transfer_not_redeemable")

        ownership_transferred = _try_transfer_ownership_best_effort(engine, row["vehicle_id"], redeemer_user_id)

        conn.execute(
            update(t)
            .where(t.c.transfer_id == row["transfer_id"])
            .values(ownership_transferred=bool(ownership_transferred))
        )

    payload = {
        "transfer_id": row["transfer_id"],
        "vehicle_id_hmac": _hmac_hex(secret, row["vehicle_id"]),
        "ownership_transferred": bool(ownership_transferred),
    }
    try:
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_REDEEMED",
            actor_user_id=redeemer_user_id,
            target_id=row["transfer_id"],
            payload=payload,
        )
    except Exception:
        pass

    return {
        "transfer_id": row["transfer_id"],
        "vehicle_id": row["vehicle_id"],
        "status": "redeemed",
        "ownership_transferred": bool(ownership_transferred),
    }


def cancel_transfer(
    *,
    db: Session,
    initiator_user_id: str,
    initiator_role: str,
    transfer_id: str,
) -> Dict[str, Any]:
    if initiator_role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    engine = _get_engine_for_sale_transfer(db)
    t = _ensure_sale_transfer_table(engine)
    secret = _get_secret_key()
    now = _utc_now()

    row = _row_by_transfer_id(engine, t, transfer_id)
    if not row:
        raise HTTPException(status_code=404, detail="transfer_not_found")

    if str(row.get("initiator_user_id")) != str(initiator_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

    row = _maybe_mark_expired(engine, t, row, now)
    if row.get("status") == "expired":
        raise HTTPException(status_code=410, detail="transfer_expired")

    if row.get("status") != "created":
        raise HTTPException(status_code=409, detail="transfer_not_cancellable")

    payload = {"transfer_id": row["transfer_id"], "vehicle_id_hmac": _hmac_hex(secret, row["vehicle_id"])}

    with engine.begin() as conn:
        res = conn.execute(
            update(t)
            .where(t.c.transfer_id == transfer_id)
            .where(t.c.status == "created")
            .values(status="cancelled", cancelled_at=now)
        )
        if getattr(res, "rowcount", 0) != 1:
            raise HTTPException(status_code=409, detail="transfer_not_cancellable")

    try:
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_CANCELLED",
            actor_user_id=initiator_user_id,
            target_id=transfer_id,
            payload=payload,
        )
    except Exception:
        pass

    return {"ok": True, "transfer_id": transfer_id, "status": "cancelled"}


def get_transfer_status(
    *,
    db: Session,
    actor_user_id: str,
    actor_role: str,
    transfer_id: str,
) -> Dict[str, Any]:
    engine = _get_engine_for_sale_transfer(db)
    t = _ensure_sale_transfer_table(engine)
    _ = _get_secret_key()
    now = _utc_now()

    row = _row_by_transfer_id(engine, t, transfer_id)
    if not row:
        raise HTTPException(status_code=404, detail="transfer_not_found")

    row = _maybe_mark_expired(engine, t, row, now)

    if actor_role in {"vip", "dealer"}:
        allowed = (
            str(row.get("initiator_user_id")) == str(actor_user_id)
            or str(row.get("redeemed_by_user_id") or "") == str(actor_user_id)
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="forbidden")
    elif actor_role in {"admin", "superadmin"}:
        pass
    else:
        raise HTTPException(status_code=403, detail="forbidden")

    def _dt(v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return _iso_z(v.replace(tzinfo=timezone.utc))
        return str(v)

    return {
        "transfer_id": row["transfer_id"],
        "vehicle_id": row["vehicle_id"],
        "status": row.get("status") or "unknown",
        "created_at": _dt(row.get("created_at")) or "",
        "expires_at": _dt(row.get("expires_at")) or "",
        "is_expired": bool(row.get("status") == "expired"),
        "redeemed_at": _dt(row.get("redeemed_at")),
        "cancelled_at": _dt(row.get("cancelled_at")),
        "redeemed_by_user_id": row.get("redeemed_by_user_id"),
        "initiator_user_id": row.get("initiator_user_id"),
        "ownership_transferred": bool(row.get("ownership_transferred") or False),
    }
