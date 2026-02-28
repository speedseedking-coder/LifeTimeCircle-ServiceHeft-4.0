import importlib.util
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


def test_admin_can_list_vip_businesses_with_staff(client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    admin_token = h._mk_token(db_path, "admin")
    super_token = h._mk_token(db_path, "superadmin")

    owner_id = h._mk_user(db_path, "vip")
    staff1 = h._mk_user(db_path, "user")
    staff2 = h._mk_user(db_path, "dealer")

    create_res = client.post(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"owner_user_id": owner_id, "business_id": "biz-demo-1"},
    )
    assert create_res.status_code == 200, create_res.text

    approve_res = client.post(
        "/admin/vip-businesses/biz-demo-1/approve",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert approve_res.status_code == 200, approve_res.text

    for staff_id in (staff1, staff2):
        staff_res = client.post(
            f"/admin/vip-businesses/biz-demo-1/staff/{staff_id}",
            headers={"Authorization": f"Bearer {super_token}"},
            json={"reason": "seed"},
        )
        assert staff_res.status_code == 200, staff_res.text

    list_res = client.get(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_res.status_code == 200, list_res.text

    payload = list_res.json()
    assert isinstance(payload, list)
    assert len(payload) == 1

    row = payload[0]
    assert row["business_id"] == "biz-demo-1"
    assert row["owner_user_id"] == owner_id
    assert row["approved"] is True
    assert row["staff_count"] == 2
    assert row["staff_user_ids"] == [staff1, staff2]


def test_non_admin_cannot_list_vip_businesses(client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)
    user_token = h._mk_token(db_path, "user")

    list_res = client.get(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert list_res.status_code == 403, list_res.text
