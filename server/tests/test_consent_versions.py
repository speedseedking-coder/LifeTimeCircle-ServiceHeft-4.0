from __future__ import annotations

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


def test_verify_does_not_require_consent_payload(tmp_path):
    settings = _mk_settings(tmp_path, terms_v="v2", privacy_v="v1", dev_otp=True)

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
        ip="127.0.0.1",
        user_agent="pytest",
        request_id="rid-2",
    )

    assert isinstance(token, str) and len(token) > 10
    assert isinstance(expires_at, str) and len(expires_at) > 10


def test_verify_ignores_required_versions_until_consent_flow(tmp_path):
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
        ip="127.0.0.1",
        user_agent="pytest",
        request_id="rid-2",
    )

    assert isinstance(token, str) and len(token) > 10
    assert isinstance(expires_at, str) and len(expires_at) > 10
