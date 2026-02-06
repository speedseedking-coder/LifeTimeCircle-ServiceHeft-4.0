$ErrorActionPreference = "Stop"

$path = Join-Path (Get-Location) "app\services\export_store.py"
if (!(Test-Path $path)) { throw "export_store.py nicht gefunden: $path (bitte im server\ Ordner ausführen)" }

$content = @'
import datetime as dt
import hmac
import os
import re
import secrets
import uuid
from hashlib import sha256
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from app.core.config import get_settings


def _safe_resource_type(resource_type: str) -> str:
    rt = (resource_type or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_]+", rt):
        rt = re.sub(r"[^a-z0-9_]+", "_", rt).strip("_")
    if not rt:
        raise ValueError("invalid_resource_type")
    return rt


def _utcnow_naive() -> dt.datetime:
    # py3.12: utcnow() warnt -> wir nehmen aware UTC und strippen tzinfo
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def _as_naive_utc(d: dt.datetime) -> dt.datetime:
    if d.tzinfo is None:
        return d
    return d.astimezone(dt.timezone.utc).replace(tzinfo=None)


def _require_secret_key() -> str:
    settings = get_settings()
    secret = getattr(settings, "secret_key", None)
    if not isinstance(secret, str) or len(secret.strip()) < 16:
        raise RuntimeError("missing_or_weak_secret_key")
    return secret.strip()


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), sha256).hexdigest()


def _ensure_table(conn: Connection, resource_type: str) -> Table:
    """
    Wichtig: KEIN globaler Cache!
    Pytest baut gern neue Engine/DB je Test -> Cache würde auf "alte" DB zeigen.
    """
    rt = _safe_resource_type(resource_type)
    table_name = f"export_grants_{rt}"

    md = MetaData()
    Table(
        table_name,
        md,
        Column("id", String(36), primary_key=True),
        Column("resource_type", String(64), nullable=False),
        Column("resource_id", String(128), nullable=False),
        Column("token_hmac", String(128), nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False),
        Column("remaining_uses", Integer, nullable=False, default=1),
        Column("issued_by_role", String(32), nullable=True),
        Column("issued_by_user_id", String(64), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )

    md.create_all(bind=conn)

    # Reflection liefert columns so, wie Dialekt sie tatsächlich abbildet
    return Table(table_name, MetaData(), autoload_with=conn)


def _ttl_seconds(default: int = 600) -> int:
    try:
        return max(1, int(os.getenv("LTC_EXPORT_TTL_SECONDS", str(default))))
    except Exception:
        return default


def _max_uses(default: int = 1) -> int:
    try:
        return max(1, int(os.getenv("LTC_EXPORT_MAX_USES", str(default))))
    except Exception:
        return default


def issue_one_time_token(
    db: Session,
    *,
    resource_type: str,
    resource_id: str,
    issued_by_role: str,
    issued_by_user_id: Optional[str],
    ttl_seconds: Optional[int] = None,
    uses: Optional[int] = None,
) -> Tuple[str, dt.datetime]:
    conn = db.connection()
    grants = _ensure_table(conn, resource_type)

    secret = _require_secret_key()
    raw_token = secrets.token_urlsafe(32)
    token_h = _hmac_hex(secret, raw_token)

    now = _utcnow_naive()
    ttl = _ttl_seconds() if ttl_seconds is None else max(1, int(ttl_seconds))
    remaining = _max_uses() if uses is None else max(1, int(uses))
    expires_at = now + dt.timedelta(seconds=ttl)

    # Wichtig: über dieselbe Connection ausführen (sqlite memory safe)
    conn.execute(
        grants.insert().values(
            id=str(uuid.uuid4()),
            resource_type=_safe_resource_type(resource_type),
            resource_id=str(resource_id),
            token_hmac=token_h,
            expires_at=expires_at,
            remaining_uses=remaining,
            issued_by_role=str(issued_by_role) if issued_by_role else None,
            issued_by_user_id=str(issued_by_user_id) if issued_by_user_id else None,
            created_at=now,
        )
    )
    db.commit()
    return raw_token, expires_at


def consume_one_time_token(
    db: Session,
    resource_type: str,
    resource_id: str,
    export_token: str,
) -> Dict[str, Any]:
    conn = db.connection()
    grants = _ensure_table(conn, resource_type)

    secret = _require_secret_key()
    token_h = _hmac_hex(secret, export_token)
    now = _utcnow_naive()

    row = conn.execute(
        select(grants)
        .where(grants.c.resource_type == _safe_resource_type(resource_type))
        .where(grants.c.resource_id == str(resource_id))
        .where(grants.c.token_hmac == token_h)
        .limit(1)
    ).mappings().first()

    if not row:
        raise PermissionError("token_invalid")

    expires_at = row.get("expires_at")
    if not isinstance(expires_at, dt.datetime):
        raise PermissionError("token_invalid")

    if _as_naive_utc(expires_at) <= now:
        raise PermissionError("token_expired")

    remaining = int(row.get("remaining_uses") or 0)
    if remaining <= 0:
        raise PermissionError("token_used")

    conn.execute(
        update(grants)
        .where(grants.c.id == row["id"])
        .values(remaining_uses=remaining - 1)
    )
    db.commit()

    return dict(row)
'@

Set-Content -Path $path -Value $content -Encoding UTF8
Write-Host "OK: export_store.py gefixt (no cache, conn.execute, ttl_seconds/uses kompatibel): $path"
