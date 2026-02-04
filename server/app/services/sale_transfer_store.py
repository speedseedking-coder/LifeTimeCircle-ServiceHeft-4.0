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
    insert,
    select,
    update,
)
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.services.sale_transfer_audit import write_sale_audit


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_secret_key() -> str:
    secret = (os.getenv("LTC_SECRET_KEY") or "").strip()
    if len(secret) < 16:
        raise RuntimeError("LTC_SECRET_KEY fehlt/zu kurz (>=16)")
    return secret


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _ensure_sale_transfer_table(db: Session) -> Table:
    bind = db.get_bind()
    if bind is None:
        raise RuntimeError("DB bind fehlt")
    insp = sa_inspect(bind)
    md = MetaData()

    name = "sale_transfers"
    if insp.has_table(name):
        return Table(name, md, autoload_with=bind)

    t = Table(
        name,
        md,
        Column("transfer_id", String(36), primary_key=True),
        Column("token_hmac", String(64), nullable=False, unique=True, index=True),
        Column("vehicle_id", String(128), nullable=False, index=True),
        Column("status", String(16), nullable=False, index=True),  # created|redeemed|cancelled|expired
        Column("created_at", DateTime(timezone=True), nullable=False, index=True),
        Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
        Column("initiator_user_id", String(36), nullable=False, index=True),
        Column("initiator_role", String(16), nullable=False),
        Column("redeemed_by_user_id", String(36), nullable=True, index=True),
        Column("redeemed_by_role", String(16), nullable=True),
        Column("redeemed_at", DateTime(timezone=True), nullable=True),
        Column("cancelled_at", DateTime(timezone=True), nullable=True),
        Column("expired_at", DateTime(timezone=True), nullable=True),
        Column("ownership_transferred", Boolean, nullable=False, server_default="0"),
    )
    md.create_all(bind=bind)
    return t


def _maybe_mark_expired(db: Session, t: Table, row: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    if row.get("status") == "created" and row.get("expires_at") and row["expires_at"] <= now:
        db.execute(
            update(t)
            .where(t.c.transfer_id == row["transfer_id"])
            .values(status="expired", expired_at=now)
        )
        row["status"] = "expired"
        row["expired_at"] = now
    return row


def _select_by_token_hmac(db: Session, t: Table, token_h: str) -> Optional[Dict[str, Any]]:
    stmt = select(t).where(t.c.token_hmac == token_h).limit(1)
    r = db.execute(stmt).mappings().first()
    return dict(r) if r else None


def _select_by_transfer_id(db: Session, t: Table, transfer_id: str) -> Optional[Dict[str, Any]]:
    stmt = select(t).where(t.c.transfer_id == transfer_id).limit(1)
    r = db.execute(stmt).mappings().first()
    return dict(r) if r else None


_OWNER_COL_CANDIDATES = ("owner_id", "user_id", "account_id", "created_by_user_id", "created_by")


def _try_transfer_ownership_best_effort(db: Session, vehicle_id: str, new_owner_user_id: str) -> bool:
    bind = db.get_bind()
    if bind is None:
        return False
    insp = sa_inspect(bind)
    names = insp.get_table_names()

    cand = []
    for n in names:
        if re.search(r"(vehicle|vehicles|servicebook|servicebooks|fahrzeug)", n, re.IGNORECASE):
            cand.append(n)

    for table_name in cand:
        try:
            t = Table(table_name, MetaData(), autoload_with=bind)
        except Exception:
            continue
        if "id" not in t.c:
            continue
        owner_col = None
        for c in _OWNER_COL_CANDIDATES:
            if c in t.c:
                owner_col = t.c[c]
                break
        if owner_col is None:
            continue

        try:
            res = db.execute(
                update(t)
                .where(t.c.id == vehicle_id)
                .values({owner_col.key: new_owner_user_id})
            )
            if getattr(res, "rowcount", 0) and res.rowcount > 0:
                return True
        except Exception:
            continue

    return False


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

    t = _ensure_sale_transfer_table(db)
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
        "expires_at": _iso_z(expires),
    }

    try:
        db.execute(
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
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_CREATED",
            actor_user_id=initiator_user_id,
            target_id=transfer_id,
            payload=payload,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "transfer_id": transfer_id,
        "transfer_token": token,
        "expires_at": _iso_z(expires),
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

    t = _ensure_sale_transfer_table(db)
    secret = _get_secret_key()
    now = _utc_now()

    token_h = _hmac_hex(secret, transfer_token)
    row = _select_by_token_hmac(db, t, token_h)

    if not row:
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_REDEEM_FAILED",
            actor_user_id=redeemer_user_id,
            target_id="unknown",
            payload={"reason": "not_found"},
        )
        db.commit()
        raise HTTPException(status_code=404, detail="transfer_not_found")

    row = _maybe_mark_expired(db, t, row, now)

    if row.get("status") == "expired":
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_REDEEM_FAILED",
            actor_user_id=redeemer_user_id,
            target_id=row["transfer_id"],
            payload={"reason": "expired"},
        )
        db.commit()
        raise HTTPException(status_code=410, detail="transfer_expired")

    if row.get("status") != "created":
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_REDEEM_FAILED",
            actor_user_id=redeemer_user_id,
            target_id=row["transfer_id"],
            payload={"reason": "not_redeemable", "status": row.get("status")},
        )
        db.commit()
        raise HTTPException(status_code=409, detail="transfer_not_redeemable")

    ownership_transferred = _try_transfer_ownership_best_effort(db, row["vehicle_id"], redeemer_user_id)

    payload = {
        "transfer_id": row["transfer_id"],
        "vehicle_id_hmac": _hmac_hex(secret, row["vehicle_id"]),
        "ownership_transferred": bool(ownership_transferred),
    }

    try:
        db.execute(
            update(t)
            .where(t.c.transfer_id == row["transfer_id"])
            .values(
                status="redeemed",
                redeemed_by_user_id=redeemer_user_id,
                redeemed_by_role=redeemer_role,
                redeemed_at=now,
                ownership_transferred=bool(ownership_transferred),
            )
        )
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_REDEEMED",
            actor_user_id=redeemer_user_id,
            target_id=row["transfer_id"],
            payload=payload,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

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

    t = _ensure_sale_transfer_table(db)
    secret = _get_secret_key()
    now = _utc_now()

    row = _select_by_transfer_id(db, t, transfer_id)
    if not row:
        raise HTTPException(status_code=404, detail="transfer_not_found")

    if str(row.get("initiator_user_id")) != str(initiator_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

    row = _maybe_mark_expired(db, t, row, now)
    if row.get("status") == "expired":
        raise HTTPException(status_code=410, detail="transfer_expired")

    if row.get("status") != "created":
        raise HTTPException(status_code=409, detail="transfer_not_cancellable")

    payload = {
        "transfer_id": row["transfer_id"],
        "vehicle_id_hmac": _hmac_hex(secret, row["vehicle_id"]),
    }

    try:
        db.execute(
            update(t)
            .where(t.c.transfer_id == transfer_id)
            .values(status="cancelled", cancelled_at=now)
        )
        write_sale_audit(
            db,
            event_type="SALE_TRANSFER_CANCELLED",
            actor_user_id=initiator_user_id,
            target_id=transfer_id,
            payload=payload,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"ok": True, "transfer_id": transfer_id, "status": "cancelled"}


def get_transfer_status(
    *,
    db: Session,
    actor_user_id: str,
    actor_role: str,
    transfer_id: str,
) -> Dict[str, Any]:
    t = _ensure_sale_transfer_table(db)
    _ = _get_secret_key()
    now = _utc_now()

    row = _select_by_transfer_id(db, t, transfer_id)
    if not row:
        raise HTTPException(status_code=404, detail="transfer_not_found")

    row = _maybe_mark_expired(db, t, row, now)

    if actor_role in {"vip", "dealer"}:
        allowed = str(row.get("initiator_user_id")) == str(actor_user_id) or str(row.get("redeemed_by_user_id") or "") == str(actor_user_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="forbidden")
    elif actor_role in {"admin", "superadmin"}:
        pass
    else:
        raise HTTPException(status_code=403, detail="forbidden")

    created_at = row.get("created_at")
    expires_at = row.get("expires_at")

    def _dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return _iso_z(v)
        return str(v)

    return {
        "transfer_id": row["transfer_id"],
        "vehicle_id": row["vehicle_id"],
        "status": row.get("status") or "unknown",
        "created_at": _dt(created_at) or "",
        "expires_at": _dt(expires_at) or "",
        "is_expired": bool(row.get("status") == "expired"),
        "redeemed_at": _dt(row.get("redeemed_at")),
        "cancelled_at": _dt(row.get("cancelled_at")),
        "redeemed_by_user_id": row.get("redeemed_by_user_id"),
        "initiator_user_id": row.get("initiator_user_id"),
        "ownership_transferred": bool(row.get("ownership_transferred") or False),
    }