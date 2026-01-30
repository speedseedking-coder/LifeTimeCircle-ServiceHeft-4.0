from __future__ import annotations

import pytest

from app.auth.settings import AuthSettings
from app.auth.service import request_challenge, verify_challenge_and_create_session


def _mk_settings(tmp_path, *, terms_v="v1", privacy_v="v1", dev_otp=True) -> AuthSettings:
    db_path = tmp_path / "app.db"
    return AuthSettings(
        secret_key="x" * 40,
        db_path=str(db_path),
        dev_expose_otp=dev_otp,
        mailer_mode="null",
        terms_version_required=terms_v,
        privacy_version_required=privacy_v,
    )


def test_verify_blocks_on_terms_version_mismatch(tmp_path):
    settings = _mk_settings(tmp_path, terms_v="v2", privacy_v="v1", dev_otp=True)

    challenge_id, dev_otp = request_challenge(
        settings,
        email="test@example.com",
        ip="127.0.0.1",
        user_agent="pytest",
        request_id="rid-1",
    )
    assert dev_otp is not None

    with pytest.raises(ValueError) as e:
        verify_challenge_and_create_session(
            settings,
            email="test@example.com",
            challenge_id=challenge_id,
            otp=dev_otp,
            consents=[
                {"doc_type": "terms", "doc_version": "v1", "accepted_at": "2026-01-01T00:00:00Z", "source": "ui"},
                {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-01-01T00:00:00Z", "source": "ui"},
            ],
            ip="127.0.0.1",
            user_agent="pytest",
            request_id="rid-2",
        )
    assert str(e.value) == "CONSENT_REQUIRED"


def test_verify_passes_on_required_versions(tmp_path):
    settings = _mk_settings(tmp_path, terms_v="v2", privacy_v="v3", dev_otp=True)

    challenge_id, dev_otp = request_challenge(
        settings,
        email="test@example.com",
        ip="127.0.0.1",
        user_agent="pytest",
        request_id="rid-1",
    )
    assert dev_otp is not None

    token, expires_at = verify_challenge_and_create_session(
        settings,
        email="test@example.com",
        challenge_id=challenge_id,
        otp=dev_otp,
        consents=[
            {"doc_type": "terms", "doc_version": "v2", "accepted_at": "2026-01-01T00:00:00Z", "source": "ui"},
            {"doc_type": "privacy", "doc_version": "v3", "accepted_at": "2026-01-01T00:00:00Z", "source": "ui"},
        ],
        ip="127.0.0.1",
        user_agent="pytest",
        request_id="rid-2",
    )

    assert isinstance(token, str) and len(token) > 10
    assert isinstance(expires_at, str) and len(expires_at) > 10
