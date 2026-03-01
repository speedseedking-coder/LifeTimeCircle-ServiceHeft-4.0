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


def test_vip_business_approve_requires_superadmin(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    admin_token = h._mk_token(db_path, "admin")
    super_token = h._mk_token(db_path, "superadmin")

    owner_id = h._mk_user(db_path, "vip")

    # create business request (admin ok)
    r_create = client.post(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"owner_user_id": owner_id, "reason": "x"},
    )
    assert r_create.status_code == 200, r_create.text
    business_id = r_create.json()["business_id"]

    # approve: admin forbidden
    r_appr_admin = client.post(
        f"/admin/vip-businesses/{business_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_appr_admin.status_code == 403, r_appr_admin.text

    # approve: superadmin ok
    r_appr_super = client.post(
        f"/admin/vip-businesses/{business_id}/approve",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_approve"),
        },
    )
    assert r_appr_super.status_code == 200, r_appr_super.text
    assert r_appr_super.json()["approved"] is True


def test_vip_business_staff_limit_max_two(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    admin_token = h._mk_token(db_path, "admin")
    super_token = h._mk_token(db_path, "superadmin")

    owner_id = h._mk_user(db_path, "vip")
    staff1 = h._mk_user(db_path, "user")
    staff2 = h._mk_user(db_path, "user")
    staff3 = h._mk_user(db_path, "user")

    # create business request
    r_create = client.post(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"owner_user_id": owner_id},
    )
    assert r_create.status_code == 200, r_create.text
    business_id = r_create.json()["business_id"]

    # adding staff before approval -> 400
    r_before = client.post(
        f"/admin/vip-businesses/{business_id}/staff/{staff1}",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_staff"),
        },
        json={"reason": "x"},
    )
    assert r_before.status_code == 400, r_before.text

    # approve
    r_appr = client.post(
        f"/admin/vip-businesses/{business_id}/approve",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_approve"),
        },
    )
    assert r_appr.status_code == 200, r_appr.text

    # add staff1 ok
    r1 = client.post(
        f"/admin/vip-businesses/{business_id}/staff/{staff1}",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_staff"),
        },
        json={"reason": "x"},
    )
    assert r1.status_code == 200, r1.text

    # add staff2 ok
    r2 = client.post(
        f"/admin/vip-businesses/{business_id}/staff/{staff2}",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_staff"),
        },
        json={"reason": "x"},
    )
    assert r2.status_code == 200, r2.text

    # add staff3 -> limit reached
    r3 = client.post(
        f"/admin/vip-businesses/{business_id}/staff/{staff3}",
        headers={
            "Authorization": f"Bearer {super_token}",
            **h._grant_step_up(client, super_token, "vip_business_staff"),
        },
        json={"reason": "x"},
    )
    assert r3.status_code == 409, r3.text
    assert r3.json().get("detail") == "staff_limit_reached"


def test_vip_business_sensitive_actions_require_step_up(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    h = _helpers()
    db_path = h._ensure_env(monkeypatch, tmp_path)

    admin_token = h._mk_token(db_path, "admin")
    super_token = h._mk_token(db_path, "superadmin")
    owner_id = h._mk_user(db_path, "vip")
    staff1 = h._mk_user(db_path, "user")

    r_create = client.post(
        "/admin/vip-businesses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"owner_user_id": owner_id},
    )
    assert r_create.status_code == 200, r_create.text
    business_id = r_create.json()["business_id"]

    r_appr = client.post(
        f"/admin/vip-businesses/{business_id}/approve",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert r_appr.status_code == 403, r_appr.text
    assert r_appr.json()["detail"] == "admin_step_up_required"

    r_staff = client.post(
        f"/admin/vip-businesses/{business_id}/staff/{staff1}",
        headers={"Authorization": f"Bearer {super_token}"},
        json={"reason": "x"},
    )
    assert r_staff.status_code == 403, r_staff.text
    assert r_staff.json()["detail"] == "admin_step_up_required"
