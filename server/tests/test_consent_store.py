# server/tests/test_consent_store.py
from __future__ import annotations


def test_consent_store_wrapper_exports_expected_symbols() -> None:
    """
    Wrapper v1 ist bewusst klein: er existiert primär als Import-Kompatibilität
    für auth/routes.py und andere Stellen.

    Erwartete Exporte (SoT / Master Checkpoint):
    - record_consent
    - get_consent_status
    - env_consent_version
    - env_db_path
    """
    import app.consent_store as cs

    assert hasattr(cs, "record_consent"), "app.consent_store.record_consent fehlt"
    assert hasattr(cs, "get_consent_status"), "app.consent_store.get_consent_status fehlt"
    assert hasattr(cs, "env_consent_version"), "app.consent_store.env_consent_version fehlt"
    assert hasattr(cs, "env_db_path"), "app.consent_store.env_db_path fehlt"
