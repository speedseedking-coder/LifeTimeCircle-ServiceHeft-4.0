import datetime as dt
import hmac
import hashlib
import os
import secrets
from typing import Any, Dict, Optional, Tuple, Union

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    select,
    insert,
    update,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session


_EXPORT_TABLE_NAME = "export_grants_vehicle"
_metadata = MetaData()

_export_grants = Table(
    _EXPORT_TABLE_NAME,
    _metadata,
    Column("id", String(64), primary_key=True),
    Column("resource_type", String(32), nullable=False),
    Column("resource_id", String(128), nullable=False),
    Column("token_hmac", String(128), nullable=False, index=True),
    Column("issued_by_role", String(32), nullable=False),
    Column("issued_by_user_id", String(128), nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("remaining_uses", Integer, nullable=False, default=1),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _require_secret_key() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("LTC_SECRET_KEY fehlt (ENV).")
    return secret


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _ensure_table(bind: Union[Engine, Connection]) -> None:
    # WICHTIG: in Tests mit sqlite :memory: muss das auf derselben Connection passieren,
    # sonst sieht die Session die Tabellen nicht.
    _metadata.create_all(bind=bind, tables=[_export_grants], checkfirst=True)


def _default_ttl_seconds() -> int:
    raw = os.environ.get("LTC_EXPORT_TTL_SECONDS", "").strip()
    if not raw:
        return 600
    try:
        v = int(raw)
    except ValueError:
        return 600
    return max(60, min(v, 3600))  # min 60s, max 1h


def _as_utc_aware(ts: dt.datetime) -> dt.datetime:
    """
    SQLite liefert oft naive datetimes zurück, auch wenn DateTime(timezone=True) gesetzt ist.
    Policy: naive => als UTC interpretieren (fail-safe für TTL).
    """
    if ts.tzinfo is None:
        return ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(dt.timezone.utc)


def issue_one_time_token(
    db: Session,
    resource_type: str,
    resource_id: str,
    issued_by_role: str,
    issued_by_user_id: Optional[str],
    ttl_seconds: Optional[int] = None,
    uses: int = 1,
) -> Tuple[str, dt.datetime]:
    # gleiche Connection nutzen (sqlite :memory: safe)
    conn = db.connection()
    _ensure_table(conn)

    secret = _require_secret_key()
    ttl = _default_ttl_seconds() if ttl_seconds is None else int(ttl_seconds)
    ttl = max(60, min(ttl, 3600))
    uses = 1 if uses <= 1 else min(int(uses), 3)  # one-time default, hard cap

    export_token = secrets.token_urlsafe(32)  # plaintext nur Response
    token_h = _hmac_hex(secret, export_token)

    now = _utcnow()
    expires_at = now + dt.timedelta(seconds=ttl)

    grant_id = secrets.token_hex(16)

    db.execute(
        insert(_export_grants).values(
            id=grant_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            token_hmac=token_h,
            issued_by_role=issued_by_role,
            issued_by_user_id=issued_by_user_id,
            expires_at=expires_at,
            remaining_uses=uses,
            created_at=now,
        )
    )
    db.commit()
    return export_token, expires_at


def consume_one_time_token(
    db: Session,
    resource_type: str,
    resource_id: str,
    export_token: str,
) -> Dict[str, Any]:
    conn = db.connection()
    _ensure_table(conn)

    secret = _require_secret_key()
    token_h = _hmac_hex(secret, export_token)
    now = _utcnow()

    row = db.execute(
        select(_export_grants)
        .where(_export_grants.c.resource_type == resource_type)
        .where(_export_grants.c.resource_id == str(resource_id))
        .where(_export_grants.c.token_hmac == token_h)
        .limit(1)
    ).mappings().first()

    if not row:
        raise PermissionError("token_invalid")

    expires_at = row.get("expires_at")
    remaining = int(row.get("remaining_uses") or 0)

    if not isinstance(expires_at, dt.datetime):
        raise PermissionError("token_invalid")

    expires_at = _as_utc_aware(expires_at)

    if expires_at <= now:
        raise PermissionError("token_expired")

    if remaining <= 0:
        raise PermissionError("token_used")

    db.execute(
        update(_export_grants)
        .where(_export_grants.c.id == row["id"])
        .values(remaining_uses=remaining - 1)
    )
    db.commit()

    return dict(row)
