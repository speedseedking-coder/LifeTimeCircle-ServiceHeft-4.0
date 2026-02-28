# Pfad: server/tests/test_sale_transfer_api.py
from __future__ import annotations

import importlib
import sqlite3
import sys
from typing import Tuple

import pytest
from fastapi.testclient import TestClient


def _ensure_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> str:
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("LTC_DB_PATH", str(db_path))
    monkeypatch.setenv("LTC_SECRET_KEY", "dev-only-change-me-32chars-min-ABCD")  # >=32
    monkeypatch.setenv("LTC_DEV_EXPOSE_OTP", "1")
    monkeypatch.setenv("LTC_MAILER_MODE", "null")
    return str(db_path)


def _load_app():
    # bei env-changes reloaden
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
        return sys.modules["app.main"].app
    from app.main import app  # type: ignore

    return app


def _auth_login(client: TestClient, email: str) -> Tuple[str, str]:
    r = client.post("/auth/request", json={"email": email})
    assert r.status_code == 200, r.text
    j = r.json()

    # request liefert i.d.R. challenge_id, wir akzeptieren auch challengeId (nur fürs Lesen)
    challenge_id = j.get("challenge_id") or j.get("challengeId")
    dev_otp = j.get("dev_otp") or j.get("otp") or j.get("devOtp")
    assert challenge_id, j
    assert dev_otp, j

    payload = {"challenge_id": challenge_id, "otp": dev_otp, "email": email}
    r2 = client.post("/auth/verify", json=payload)
    assert r2.status_code == 200, r2.text

    j2 = r2.json()
    token = j2.get("access_token") or j2.get("token") or j2.get("accessToken")
    assert token, j2

    r3 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200, r3.text
    me = r3.json()
    user_id = me.get("user_id") or me.get("userId") or me.get("id")
    assert user_id, me
    return token, str(user_id)


def _set_role(db_path: str, user_id: str, role: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE auth_users SET role=? WHERE user_id=?;", (role, user_id))
        conn.commit()
    finally:
        conn.close()


def test_sale_transfer_create_redeem_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_a, uid_a = _auth_login(client, "vip@example.com")
    _set_role(db_path, uid_a, "vip")

    tok_b, uid_b = _auth_login(client, "dealer@example.com")
    _set_role(db_path, uid_b, "dealer")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-1"},
        headers={"Authorization": f"Bearer {tok_a}"},
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["status"] == "created"
    assert out["transfer_id"]
    assert out["transfer_token"]
    assert out["expires_at"]

    token = out["transfer_token"]
    tid = out["transfer_id"]

    # Initiator darf Status sehen
    rs_a_pre = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_a}"})
    assert rs_a_pre.status_code == 200, rs_a_pre.text

    # VOR Redeem: Dealer ist noch kein Teilnehmer -> 403 (object-level gate)
    rs_b_pre = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert rs_b_pre.status_code == 403, rs_b_pre.text

    r2 = client.post(
        "/sale/transfer/redeem",
        json={"transfer_token": token},
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert r2.status_code == 200, r2.text
    out2 = r2.json()
    assert out2["transfer_id"] == tid
    assert out2["vehicle_id"] == "veh-1"
    assert out2["status"] == "redeemed"
    assert "ownership_transferred" in out2

    # Nach Redeem: Dealer ist Redeemer -> 200
    rs_b_post = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert rs_b_post.status_code == 200, rs_b_post.text

    # Double-redeem block
    r3 = client.post(
        "/sale/transfer/redeem",
        json={"transfer_token": token},
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert r3.status_code in (409, 410), r3.text

    # Initiator weiterhin ok
    rs_a_post = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_a}"})
    assert rs_a_post.status_code == 200, rs_a_post.text


def test_sale_transfer_rbac_blocks_user_and_admin_create(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_u, uid_u = _auth_login(client, "user@example.com")
    _set_role(db_path, uid_u, "user")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-x"},
        headers={"Authorization": f"Bearer {tok_u}"},
    )
    assert r.status_code == 403, r.text

    tok_adm, uid_adm = _auth_login(client, "admin@example.com")
    _set_role(db_path, uid_adm, "admin")

    r2 = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-x"},
        headers={"Authorization": f"Bearer {tok_adm}"},
    )
    assert r2.status_code == 403, r2.text


def test_sale_transfer_status_admin_forbidden(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _ensure_env(monkeypatch, tmp_path)
    app = _load_app()
    client = TestClient(app)

    tok_v, uid_v = _auth_login(client, "vip2@example.com")
    _set_role(db_path, uid_v, "vip")

    r = client.post(
        "/sale/transfer/create",
        json={"vehicle_id": "veh-2"},
        headers={"Authorization": f"Bearer {tok_v}"},
    )
    assert r.status_code == 200, r.text
    tid = r.json()["transfer_id"]

    tok_adm, uid_adm = _auth_login(client, "admin2@example.com")
    _set_role(db_path, uid_adm, "admin")

    rs = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_adm}"})
    assert rs.status_code == 403, rs.text
