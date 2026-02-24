from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, inspect, select, update
from sqlalchemy.orm import Session

from app.routers.export_vehicle import get_actor, get_db

from app.guards import forbid_moderator
router = APIRouter(prefix="/export/user", tags=["export"], dependencies=[Depends(forbid_moderator)])
def _role_of(actor: Any) -> str:
    if actor is None:
        return ""
    if hasattr(actor, "role"):
        return str(getattr(actor, "role") or "")
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return ""


def _user_id_of(actor: Any) -> str:
    if actor is None:
        return ""
    for attr in ("user_id", "uid", "id", "sub"):
        if hasattr(actor, attr):
            v = getattr(actor, attr)
            if v:
                return str(v)
    if isinstance(actor, dict):
        for key in ("user_id", "uid", "id", "sub"):
            v = actor.get(key)
            if v:
                return str(v)
    return ""


def _require_superadmin(actor: Any) -> None:
    if _role_of(actor) != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")


def _deny_moderator(actor: Any) -> None:
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_secret() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "")
    if len(secret) < 16:
        raise HTTPException(status_code=500, detail="server_misconfigured")
    return secret


def _hmac_value(value: str) -> str:
    return hmac.new(_get_secret().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


_grant_lock = threading.Lock()
_grant_cache: Dict[int, Table] = {}


def _grants_table(db: Session) -> Table:
    engine = db.get_bind()
    key = id(engine)

    with _grant_lock:
        cached = _grant_cache.get(key)
        if cached is not None:
            return cached

        md = MetaData()
        insp = inspect(engine)
        if insp.has_table("export_grants_user"):
            tbl = Table("export_grants_user", md, autoload_with=engine)
            _grant_cache[key] = tbl
            return tbl

        tbl = Table(
            "export_grants_user",
            md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("export_token", String(255), nullable=False, unique=True, index=True),
            Column("user_id", String(255), nullable=False, index=True),
            Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
            Column("used", Boolean, nullable=False, default=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        md.create_all(engine, tables=[tbl])
        _grant_cache[key] = tbl
        return tbl


def _users_table(db: Session) -> Table:
    engine = db.get_bind()
    md = MetaData()
    insp = inspect(engine)
    for name in ("auth_users", "users", "user"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=engine)
    raise HTTPException(status_code=404, detail="not_found")


def _fetch_user_row(db: Session, user_id: str) -> Tuple[Dict[str, Any], Table]:
    tbl = _users_table(db)
    candidate_cols = [c for c in ("user_id", "id", "public_id", "uid", "sub") if c in tbl.c]
    for col in candidate_cols:
        row = db.execute(select(tbl).where(tbl.c[col] == user_id)).mappings().first()
        if row is not None:
            return dict(row), tbl
    raise HTTPException(status_code=404, detail="not_found")


def _enforce_redacted_access(actor: Any, target_user_id: str) -> None:
    role = _role_of(actor)
    if role in {"admin", "superadmin"}:
        return

    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    if _user_id_of(actor) != str(target_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

def _read_expires_at(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).replace(tzinfo=None)
        except Exception:
            return None
    return None


def _redacted_user(row: Dict[str, Any], target_user_id: str) -> Dict[str, Any]:
    blocked_contains = (
        "email",
        "phone",
        "tel",
        "name",
        "address",
        "street",
        "zip",
        "city",
        "secret",
        "password",
        "token",
    )
    out: Dict[str, Any] = {"user_id": target_user_id, "_redacted": True}

    for key, value in row.items():
        k = key.lower()
        if any(x in k for x in blocked_contains):
            continue
        if k in {"created_at", "role", "status", "id", "user_id"}:
            out[key] = value

    email_hmac = row.get("email_hmac")
    if email_hmac:
        out["email_hmac"] = str(email_hmac)
    elif row.get("email"):
        out["email_hmac"] = _hmac_value(str(row.get("email")))

    out["user_id_hmac"] = _hmac_value(target_user_id)
    return out


@router.get("/{user_id}")
def export_user_redacted(user_id: str, request: Request, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)
        _enforce_redacted_access(actor, resolved_user_id)
        data = {
            "target": "user",
            "id": resolved_user_id,
            "_redacted": True,
            "user": _redacted_user(row, resolved_user_id),
        }
        return {"data": data}
    finally:
        db.close()


@router.post("/{user_id}/grant")
def export_user_grant(user_id: str, request: Request, ttl_seconds: int = 300, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    _require_superadmin(actor)
    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)

        ttl = max(30, min(int(ttl_seconds), 3600))
        tok = secrets.token_urlsafe(32)
        now = _utcnow_naive()
        exp = now + timedelta(seconds=ttl)

        grants = _grants_table(db)
        db.execute(
            grants.insert().values(
                export_token=tok,
                user_id=resolved_user_id,
                expires_at=exp,
                used=0,
                created_at=now,
            )
        )
        db.commit()
        return {
            "user_id": resolved_user_id,
            "export_token": tok,
            "token": tok,
            "expires_at": exp.isoformat(),
            "ttl_seconds": ttl,
            "one_time": True,
            "header": "X-Export-Token",
        }
    finally:
        db.close()


@router.get("/{user_id}/full")
def export_user_full(
    user_id: str,
    request: Request,
    x_export_token: Optional[str] = Header(default=None, convert_underscores=False, alias="X-Export-Token"),
    actor: Any = Depends(get_actor),
):
    _deny_moderator(actor)
    _require_superadmin(actor)

    if not x_export_token:
        raise HTTPException(status_code=400, detail="missing_export_token")

    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)

        grants = _grants_table(db)
        g = db.execute(select(grants).where(grants.c.export_token == x_export_token)).mappings().first()
        if g is None:
            raise HTTPException(status_code=403, detail="forbidden")
        if str(g.get("user_id") or "") != resolved_user_id:
            raise HTTPException(status_code=403, detail="forbidden")

        exp = _read_expires_at(g.get("expires_at"))
        if exp is None or _utcnow_naive() > exp:
            raise HTTPException(status_code=403, detail="forbidden")

        if int(g.get("used") or 0) != 0:
            raise HTTPException(status_code=403, detail="forbidden")

        payload = {
            "target": "user",
            "id": resolved_user_id,
            "user": row,
            "data": {"user": row},
            "exported_at": _utcnow().isoformat(),
        }
        f = Fernet(_derive_fernet_key(_get_secret()))
        ciphertext = f.encrypt(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=_json_default).encode("utf-8")
        ).decode("utf-8")

        db.execute(update(grants).where(grants.c.id == g["id"]).values(used=1))
        db.commit()

        return {"user_id": resolved_user_id, "ciphertext": ciphertext, "alg": "fernet", "one_time": True}
    finally:
        db.close()
