# Pfad: server/scripts/patch_sale_transfer_router.ps1
$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$serverRoot = Split-Path -Parent $PSScriptRoot

$routerPath = Join-Path $serverRoot "app\routers\sale_transfer.py"
$storePath  = Join-Path $serverRoot "app\services\sale_transfer_store.py"
$auditPath  = Join-Path $serverRoot "app\services\sale_transfer_audit.py"
$testPath   = Join-Path $serverRoot "tests\test_sale_transfer_api.py"

$routerContent = @'
from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import Actor, require_roles
from app.db.session import get_db
from app.guards import forbid_moderator
from app.services.sale_transfer_store import (
    cancel_transfer,
    create_transfer,
    get_transfer_status,
    redeem_transfer,
)

router = APIRouter(
    prefix="/sale/transfer",
    tags=["sale_transfer"],
    dependencies=[Depends(forbid_moderator)],
)


def _actor_user_id(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("user_id") or actor.get("id") or actor.get("subject_id") or actor.get("sub") or "")
    for key in ("user_id", "id", "subject_id", "sub"):
        v = getattr(actor, key, None)
        if v:
            return str(v)
    return ""


def _actor_role(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return str(getattr(actor, "role", "") or "")


class SaleTransferCreateIn(BaseModel):
    vehicle_id: str = Field(min_length=1, max_length=128)
    ttl_seconds: Optional[int] = Field(default=None, ge=60, le=7 * 24 * 3600)


class SaleTransferCreateOut(BaseModel):
    transfer_id: str
    transfer_token: str
    expires_at: str  # ISO8601 UTC (Z)
    status: str


class SaleTransferRedeemIn(BaseModel):
    transfer_token: str = Field(min_length=20, max_length=256)


class SaleTransferRedeemOut(BaseModel):
    transfer_id: str
    vehicle_id: str
    status: str
    ownership_transferred: bool


class SaleTransferCancelIn(BaseModel):
    transfer_id: str = Field(min_length=1, max_length=64)


class SaleTransferCancelOut(BaseModel):
    ok: bool
    transfer_id: str
    status: str


class SaleTransferStatusOut(BaseModel):
    transfer_id: str
    vehicle_id: str
    status: str
    created_at: str
    expires_at: str
    is_expired: bool
    redeemed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    redeemed_by_user_id: Optional[str] = None
    initiator_user_id: str
    ownership_transferred: bool


@router.post("/create", response_model=SaleTransferCreateOut)
def sale_transfer_create(
    payload: SaleTransferCreateIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferCreateOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = create_transfer(
        db=db,
        initiator_user_id=uid,
        initiator_role=role,
        vehicle_id=payload.vehicle_id,
        ttl_seconds=payload.ttl_seconds,
    )
    return SaleTransferCreateOut(**out)


@router.post("/redeem", response_model=SaleTransferRedeemOut)
def sale_transfer_redeem(
    payload: SaleTransferRedeemIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferRedeemOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = redeem_transfer(
        db=db,
        redeemer_user_id=uid,
        redeemer_role=role,
        transfer_token=payload.transfer_token,
    )
    return SaleTransferRedeemOut(**out)


@router.post("/cancel", response_model=SaleTransferCancelOut)
def sale_transfer_cancel(
    payload: SaleTransferCancelIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferCancelOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = cancel_transfer(
        db=db,
        initiator_user_id=uid,
        initiator_role=role,
        transfer_id=payload.transfer_id,
    )
    return SaleTransferCancelOut(**out)


@router.get("/status/{transfer_id}", response_model=SaleTransferStatusOut)
def sale_transfer_status(
    transfer_id: str,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer", "admin", "superadmin"))],
) -> SaleTransferStatusOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer", "admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = get_transfer_status(
        db=db,
        actor_user_id=uid,
        actor_role=role,
        transfer_id=transfer_id,
    )
    return SaleTransferStatusOut(**out)
'@

$storeContent = @'
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
'@

$auditContent = @'
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, insert
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _pick_audit_table(db: Session) -> Table:
    bind = db.get_bind()
    if bind is None:
        raise RuntimeError("DB bind fehlt")

    insp = sa_inspect(bind)
    md = MetaData()

    for name in ("audit_events", "audit", "audits"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=bind)

    name = "sale_transfer_audit_events"
    if insp.has_table(name):
        return Table(name, md, autoload_with=bind)

    t = Table(
        name,
        md,
        Column("event_id", String(36), primary_key=True),
        Column("at", DateTime(timezone=True), nullable=False, index=True),
        Column("event_type", String(64), nullable=False, index=True),
        Column("actor_id", String(64), nullable=True, index=True),
        Column("target_id", String(64), nullable=True, index=True),
        Column("payload_json", Text, nullable=True),
    )
    md.create_all(bind=bind)
    return t


def write_sale_audit(
    db: Session,
    *,
    event_type: str,
    actor_user_id: str,
    target_id: str,
    payload: Dict[str, Any],
) -> None:
    t = _pick_audit_table(db)
    now = _utc_now()
    cols = set(c.name for c in t.c)

    values: Dict[str, Any] = {}

    if "event_id" in cols:
        values["event_id"] = str(uuid.uuid4())
    elif "id" in cols:
        values["id"] = str(uuid.uuid4())

    if "at" in cols:
        values["at"] = now
    elif "created_at" in cols:
        values["created_at"] = now
    elif "timestamp" in cols:
        values["timestamp"] = now

    if "event_name" in cols:
        values["event_name"] = event_type
    elif "event_type" in cols:
        values["event_type"] = event_type
    elif "action" in cols:
        values["action"] = event_type

    if "actor_id" in cols:
        values["actor_id"] = actor_user_id
    elif "actor_user_id" in cols:
        values["actor_user_id"] = actor_user_id

    if "target_id" in cols:
        values["target_id"] = target_id
    elif "resource_id" in cols:
        values["resource_id"] = target_id

    if "result" in cols and "result" not in values:
        values["result"] = "success"

    if "correlation_id" in cols:
        values["correlation_id"] = str(uuid.uuid4())
    if "idempotency_key" in cols:
        values["idempotency_key"] = "n/a"

    if "payload_json" in cols:
        values["payload_json"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif "details_json" in cols:
        values["details_json"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif "details" in cols:
        values["details"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    db.execute(insert(t).values(**values))
'@

$testContent = @'
from __future__ import annotations

import importlib
import sqlite3
import sys
from typing import Tuple

import pytest
from fastapi.testclient import TestClient


def _ensure_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> str:
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("LTC_DB_PATH", str(db_path))
    monkeypatch.setenv("LTC_SECRET_KEY", "dev-only-change-me-32chars-min-ABCD")
    monkeypatch.setenv("LTC_DEV_EXPOSE_OTP", "1")
    monkeypatch.setenv("LTC_MAILER_MODE", "null")
    return str(db_path)


def _load_app():
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
        return sys.modules["app.main"].app
    from app.main import app  # type: ignore
    return app


def _auth_login(client: TestClient, email: str) -> Tuple[str, str]:
    r = client.post("/auth/request", json={"email": email})
    assert r.status_code == 200, r.text
    j = r.json()
    challenge_id = j.get("challenge_id") or j.get("challengeId")
    dev_otp = j.get("dev_otp") or j.get("otp") or j.get("devOtp")
    assert challenge_id, j
    assert dev_otp, j

    r2 = client.post("/auth/verify", json={"challenge_id": challenge_id, "otp": dev_otp})
    assert r2.status_code == 200, r2.text
    j2 = r2.json()
    token = j2.get("access_token") or j2.get("token") or j2.get("accessToken")
    assert token, j2

    r3 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200, r3.text
    me = r3.json()
    user_id = me.get("user_id") or me.get("userId") or me.get("id")
    assert user_id, me
    return token, str(user_id)


def _set_role(db_path: str, user_id: str, role: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE auth_users SET role=? WHERE user_id=?;", (role, user_id))
        conn.commit()
    finally:
        conn.close()


def test_sale_transfer_create_redeem_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_a, uid_a = _auth_login(client, "vip@example.com")
    _set_role(db_path, uid_a, "vip")

    tok_b, uid_b = _auth_login(client, "dealer@example.com")
    _set_role(db_path, uid_b, "dealer")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-1"},
        headers={"Authorization": f"Bearer {tok_a}"},
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["status"] == "created"
    assert out["transfer_id"]
    assert out["transfer_token"]
    assert out["expires_at"]

    token = out["transfer_token"]
    tid = out["transfer_id"]

    r2 = client.post(
        "/sale/transfer/redeem",
        json={"transfer_token": token},
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert r2.status_code == 200, r2.text
    out2 = r2.json()
    assert out2["transfer_id"] == tid
    assert out2["vehicle_id"] == "veh-1"
    assert out2["status"] == "redeemed"
    assert "ownership_transferred" in out2

    r3 = client.post(
        "/sale/transfer/redeem",
        json={"transfer_token": token},
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert r3.status_code in (409, 410), r3.text

    rs = client.get(
        f"/sale/transfer/status/{tid}",
        headers={"Authorization": f"Bearer {tok_a}"},
    )
    assert rs.status_code == 200, rs.text

    rs2 = client.get(
        f"/sale/transfer/status/{tid}",
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert rs2.status_code == 200, rs2.text


def test_sale_transfer_rbac_blocks_user_and_admin_create(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_u, uid_u = _auth_login(client, "user@example.com")
    _set_role(db_path, uid_u, "user")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-x"},
        headers={"Authorization": f"Bearer {tok_u}"},
    )
    assert r.status_code == 403, r.text

    tok_adm, uid_adm = _auth_login(client, "admin@example.com")
    _set_role(db_path, uid_adm, "admin")

    r2 = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-x"},
        headers={"Authorization": f"Bearer {tok_adm}"},
    )
    assert r2.status_code == 403, r2.text


def test_sale_transfer_status_admin_can_read(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_v, uid_v = _auth_login(client, "vip2@example.com")
    _set_role(db_path, uid_v, "vip")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-2"},
        headers={"Authorization": f"Bearer {tok_v}"},
    )
    assert r.status_code == 200, r.text
    tid = r.json()["transfer_id"]

    tok_adm, uid_adm = _auth_login(client, "admin2@example.com")
    _set_role(db_path, uid_adm, "admin")

    rs = client.get(
        f"/sale/transfer/status/{tid}",
        headers={"Authorization": f"Bearer {tok_adm}"},
    )
    assert rs.status_code == 200, rs.text
'@

Write-FileUtf8NoBom $routerPath $routerContent
Write-FileUtf8NoBom $storePath  $storeContent
Write-FileUtf8NoBom $auditPath  $auditContent
Write-FileUtf8NoBom $testPath   $testContent

# Patch main.py: Router import + include_router
$mainPath = Join-Path $serverRoot "app\main.py"
if (!(Test-Path $mainPath)) { throw "main.py nicht gefunden: $mainPath" }

$main = Get-Content -Raw $mainPath

if ($main -notmatch "sale_transfer_router") {
  # Import einfügen
  if ($main -match "from app\.routers\.consent import router as consent_router") {
    $main = $main -replace "from app\.routers\.consent import router as consent_router", "from app.routers.consent import router as consent_router`r`nfrom app.routers.sale_transfer import router as sale_transfer_router"
  }
  elseif ($main -match "from app\.routers\.[a-zA-Z0-9_]+ import router as [a-zA-Z0-9_]+") {
    $main = [regex]::Replace(
      $main,
      "(from app\.routers\.[a-zA-Z0-9_]+ import router as [a-zA-Z0-9_]+)",
      "`$1`r`nfrom app.routers.sale_transfer import router as sale_transfer_router",
      1
    )
  }
  else {
    if ($main -match "from fastapi import .*") {
      $main = [regex]::Replace(
        $main,
        "(from fastapi import[^\r\n]+[\r\n]+)",
        "`$1from app.routers.sale_transfer import router as sale_transfer_router`r`n",
        1
      )
    } else {
      $main = "from app.routers.sale_transfer import router as sale_transfer_router`r`n" + $main
    }
  }

  # include_router einfügen
  if ($main -match "app\.include_router\(consent_router\)") {
    $main = $main -replace "app\.include_router\(consent_router\)", "app.include_router(consent_router)`r`napp.include_router(sale_transfer_router)"
  }
  else {
    $matches = [regex]::Matches($main, "(?m)^\s*app\.include_router\([^\)]*\)\s*$")
    if ($matches.Count -gt 0) {
      $last = $matches[$matches.Count - 1]
      $insertAt = $last.Index + $last.Length
      $main = $main.Insert($insertAt, "`r`napp.include_router(sale_transfer_router)")
    }
    else {
      $main = $main + "`r`napp.include_router(sale_transfer_router)`r`n"
    }
  }

  Write-FileUtf8NoBom $mainPath $main
  Write-Host "OK: main.py gepatcht (sale_transfer_router import + include_router)"
} else {
  Write-Host "SKIP: main.py enthält sale_transfer_router bereits"
}

Write-Host "OK: Sale/Transfer Dateien angelegt:"
Write-Host " - $routerPath"
Write-Host " - $storePath"
Write-Host " - $auditPath"
Write-Host " - $testPath"

