from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from .redaction import redact_metadata

@dataclass(frozen=True)
class SecurityEvent:
    ts: str
    event: str
    request_id: str
    route: str
    method: str
    status_code: int
    actor_role: str
    metadata_redacted: dict

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def emit_security_event(
    *,
    logger,
    event: str,
    request_id: str,
    route: str,
    method: str,
    status_code: int,
    actor_role: str = "unknown",
    metadata: dict | None = None,
    allowlist: set[str] | None = None,
) -> None:
    payload = SecurityEvent(
        ts=_utc_now_iso(),
        event=event,
        request_id=request_id,
        route=route,
        method=method,
        status_code=int(status_code),
        actor_role=actor_role or "unknown",
        metadata_redacted=redact_metadata(metadata, allowlist=allowlist),
    )

    # structured JSON log line (PII-safe)
    logger.info("security_telemetry %s", json.dumps(payload.__dict__, ensure_ascii=False, separators=(",", ":")))

def map_status_to_event(status_code: int) -> str | None:
    if status_code == 401:
        return "auth_unauthorized"
    if status_code == 403:
        return "rbac_forbidden"
    if status_code == 429:
        return "rate_limited"
    return None
