import importlib.util
import uuid
from pathlib import Path

import pytest
from starlette.testclient import TestClient


def _helpers():
    helper_path = Path(__file__).with_name("test_admin_role_set.py")
    spec = importlib.util.spec_from_file_location("role_set_helpers", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Kann Helper-Datei nicht laden: {helper_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_admin_can_accredit_moderator_endpoint(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    admin_token = h._mk_token(db_path, "admin")
    target_user_id = h._mk_user(db_path, "user")

    resp = client.post(
        f"/admin/users/{target_user_id}/moderator",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Idempotency-Key": uuid.uuid4().hex,
            "X-Idempotency-Key": uuid.uuid4().hex,
        },
        json={"reason": "accredit moderator"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["user_id"] == target_user_id
    assert data["new_role"] == "moderator"


def test_non_admin_cannot_accredit_moderator_endpoint(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    user_token = h._mk_token(db_path, "user")
    target_user_id = h._mk_user(db_path, "user")

    resp = client.post(
        f"/admin/users/{target_user_id}/moderator",
        headers={
            "Authorization": f"Bearer {user_token}",
            "Idempotency-Key": uuid.uuid4().hex,
            "X-Idempotency-Key": uuid.uuid4().hex,
        },
        json={"reason": "accredit moderator"},
    )
    assert resp.status_code == 403, resp.text


def test_unauthenticated_cannot_accredit_moderator_endpoint(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    target_user_id = h._mk_user(db_path, "user")

    resp = client.post(
        f"/admin/users/{target_user_id}/moderator",
        headers={
            "Idempotency-Key": uuid.uuid4().hex,
            "X-Idempotency-Key": uuid.uuid4().hex,
        },
        json={"reason": "accredit moderator"},
    )
    assert resp.status_code == 401, resp.text
