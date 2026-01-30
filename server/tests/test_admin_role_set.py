from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.auth.crypto import token_hash as token_hash_fn
from app.auth.storage import db, init_db, insert_session, upsert_user


TEST_SECRET = "x" * 40


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _ensure_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> str:
    db_path = str(tmp_path / "app.db")
    monkeypatch.setenv("LTC_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("LTC_DB_PATH", db_path)
    monkeypatch.setenv("LTC_DEV_EXPOSE_OTP", "false")
    monkeypatch.setenv("LTC_MAILER_MODE", "null")
    monkeypatch.setenv("LTC_TERMS_VERSION", "v1")
    monkeypatch.setenv("LTC_PRIVACY_VERSION", "v1")
    return db_path


def _mk_token(db_path: str, role: str) -> str:
    init_db(db_path)

    user_id = str(uuid.uuid4())
    email_hmac = "hmac_" + uuid.uuid4().hex
    created_at = _iso(_utc_now())

    raw_token = "t_" + uuid.uuid4().hex
    token_hash = token_hash_fn(TEST_SECRET, raw_token)

    session_id = str(uuid.uuid4())
    now = _utc_now()
    expires_at = _iso(now + timedelta(hours=6))

    with db(db_path) as conn:
        upsert_user(conn, user_id=user_id, email_hmac=email_hmac, created_at=created_at)
        conn.execute("UPDATE auth_users SET role = ? WHERE user_id = ?;", (role, user_id))
        insert_session(
            conn,
            session_id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            created_at=_iso(now),
            expires_at=expires_at,
        )

    return raw_token


def _mk_user(db_path: str, role: str = "user") -> str:
    init_db(db_path)

    user_id = str(uuid.uuid4())
    email_hmac = "hmac_" + uuid.uuid4().hex
    created_at = _iso(_utc_now())

    with db(db_path) as conn:
        upsert_user(conn, user_id=user_id, email_hmac=email_hmac, created_at=created_at)
        conn.execute("UPDATE auth_users SET role = ? WHERE user_id = ?;", (role, user_id))

    return user_id


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _ensure_env(monkeypatch, tmp_path)
    from app.main import create_app
    return TestClient(create_app())


def _get_role(db_path: str, user_id: str) -> str:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT role FROM auth_users WHERE user_id=?;", (user_id,)).fetchone()
        return (row[0] if row else "")
    finally:
        conn.close()


def _has_auth_audit(db_path: str, target_user_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='auth_audit_events' LIMIT 1;"
        ).fetchone()
        if not row:
            return False
        row2 = conn.execute(
            "SELECT 1 FROM auth_audit_events WHERE target_user_id=? LIMIT 1;",
            (target_user_id,),
        ).fetchone()
        return row2 is not None
    finally:
        conn.close()


def test_admin_can_set_role_and_audit(client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = _ensure_env(monkeypatch, tmp_path)

    admin_token = _mk_token(db_path, "admin")
    target_user_id = _mk_user(db_path, "user")

    resp = client.post(
        f"/admin/users/{target_user_id}/role",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Idempotency-Key": uuid.uuid4().hex,
            "X-Idempotency-Key": uuid.uuid4().hex,
        },
        json={"role": "vip", "reason": "test"},
    )
    assert resp.status_code == 200, resp.text

    assert _get_role(db_path, target_user_id) == "vip"
    assert _has_auth_audit(db_path, target_user_id) is True


def test_non_admin_cannot_set_role(client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = _ensure_env(monkeypatch, tmp_path)

    user_token = _mk_token(db_path, "user")
    target_user_id = _mk_user(db_path, "user")

    resp = client.post(
        f"/admin/users/{target_user_id}/role",
        headers={
            "Authorization": f"Bearer {user_token}",
            "Idempotency-Key": uuid.uuid4().hex,
            "X-Idempotency-Key": uuid.uuid4().hex,
        },
        json={"role": "vip", "reason": "test"},
    )
    assert resp.status_code == 403, resp.text
