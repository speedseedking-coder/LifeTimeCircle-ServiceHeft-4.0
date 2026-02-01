# server/tests/test_consent_store.py
from __future__ import annotations

from app.consent_store import ensure_consent_table, has_consent, record_consent, get_consent_status


def test_consent_store_roundtrip(tmp_path):
    db_path = str(tmp_path / "app.db")
    ensure_consent_table(db_path)

    user_id = "51712efa-a03c-484c-b899-9521c3cf898a"
    v1 = "2026-01-27"
    v2 = "2026-02-01"

    assert has_consent(db_path, user_id, v1) is False

    ts1 = record_consent(db_path, user_id, v1, source="web")
    assert isinstance(ts1, str) and ts1
    assert has_consent(db_path, user_id, v1) is True

    # idempotent: gleicher key soll nicht "neuen" timestamp erzwingen
    ts1b = record_consent(db_path, user_id, v1, source="app")
    assert ts1b == ts1

    ts2 = record_consent(db_path, user_id, v2, source="app")
    assert ts2 and ts2 != ts1

    st = get_consent_status(db_path, user_id, required_version=v2)
    assert st.required_version == v2
    assert st.has_required is True
    assert st.latest_version == v2
    assert st.latest_accepted_at == ts2
    assert st.latest_source in ("app", "web", "api", "unknown")
