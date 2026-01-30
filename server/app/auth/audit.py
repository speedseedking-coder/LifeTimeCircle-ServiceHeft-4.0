from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .storage import audit_insert


DISALLOWED_META_KEYS = {
    "email",
    "phone",
    "name",
    "address",
    "vin",
    "wid",
    "ip",
    "userAgent",
    "otp",
    "code",
    "token",
    "magicLink",
    "password",
    "accessToken",
    "refreshToken",
    "content",
    "body",
    "filename",
    "file_name",
    "title",
}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_meta(meta: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not meta:
        return None
    out: Dict[str, Any] = {}
    for k, v in meta.items():
        if not k or k in DISALLOWED_META_KEYS:
            continue
        if isinstance(v, str):
            s = v.strip()
            if not s or len(s) > 120 or "@" in s:
                continue
            out[k] = s
        elif isinstance(v, (int, float, bool)) or v is None:
            out[k] = v
    return out or None


def write_audit(
    conn,
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[str],
    scope: str,
    result: str,
    request_id: str,
    correlation_id: Optional[str] = None,
    reason_code: Optional[str] = None,
    redacted_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    audit_insert(
        conn,
        event_id=str(uuid.uuid4()),
        created_at=_utc_iso(),
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        scope=scope,
        result=result,
        request_id=request_id,
        correlation_id=correlation_id,
        reason_code=reason_code,
        redacted_metadata=sanitize_meta(redacted_metadata),
    )
