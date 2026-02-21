import json
import re
from unittest.mock import MagicMock

from app.security.redaction import redact_metadata
from app.security.telemetry import emit_security_event, map_status_to_event

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

def test_redaction_deny_by_default():
    assert redact_metadata({"foo": "bar"}) == {}

def test_redaction_allowlist_and_forbidden():
    md = {"route_name": "x", "email": "a@b.c", "token": "t", "vin": "1"}
    out = redact_metadata(md, allowlist={"route_name", "email"})
    assert out == {"route_name": "x"}  # email dropped because forbidden

def test_map_status_to_event():
    assert map_status_to_event(401) == "auth_unauthorized"
    assert map_status_to_event(403) == "rbac_forbidden"
    assert map_status_to_event(429) == "rate_limited"
    assert map_status_to_event(500) is None

def test_emit_security_event_no_pii_in_payload():
    logger = MagicMock()
    emit_security_event(
        logger=logger,
        event="auth_unauthorized",
        request_id="123e4567-e89b-12d3-a456-426614174000",
        route="/api/x",
        method="GET",
        status_code=401,
        actor_role="user",
        metadata={"email":"a@b.c","authorization":"Bearer abc","route_name":"x"},
        allowlist={"route_name","email","authorization"},
    )
    assert logger.info.called
    msg = logger.info.call_args[0][1]
    payload = json.loads(msg)
    assert payload["event"] == "auth_unauthorized"
    assert payload["request_id"] == "123e4567-e89b-12d3-a456-426614174000"
    # redaction drops forbidden keys even if allowlisted
    assert payload["metadata_redacted"] == {"route_name": "x"}
    s = json.dumps(payload)
    assert "Bearer" not in s
    assert "authorization" not in s
    assert "email" not in s
