# Pfad: server/tests/test_sale_transfer_api.py
from __future__ import annotations

import importlib
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import pytest
from fastapi.testclient import TestClient


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _fetch_consents_for_verify(client: TestClient) -> List[Dict[str, str]]:
    """
    /auth/verify erwartet: consents = [{doc_type, doc_version, accepted_at}, ...]
    Wir holen /consent/current (public) und normalisieren. Fallback: terms/privacy v1.
    """
    accepted_at = _iso_now()
    fallback = [
        {"doc_type": "terms", "doc_version": "v1", "accepted_at": accepted_at},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": accepted_at},
    ]

    r = client.get("/consent/current")
    if r.status_code != 200:
        return fallback

    data: Any = r.json()
    docs: Any = None

    if isinstance(data, list):
        docs = data
    elif isinstance(data, dict):
        for k in ("documents", "docs", "consents", "required", "items"):
            if k in data and isinstance(data[k], list):
                docs = data[k]
                break

    out: List[Dict[str, str]] = []

    if isinstance(docs, list):
        for d in docs:
            if not isinstance(d, dict):
                continue
            dt = d.get("doc_type") or d.get("type") or d.get("docType") or d.get("name")
            dv = d.get("doc_version") or d.get("version") or d.get("docVersion")
            if dt and dv:
                out.append({"doc_type": str(dt), "doc_version": str(dv), "accepted_at": accepted_at})

    # Alternative dict-shapes
    if not out and isinstance(data, dict):
        for dt in ("terms", "privacy"):
            v = None
            if isinstance(data.get(dt), str):
                v = data.get(dt)
            elif isinstance(data.get(dt), dict):
                v = data[dt].get("version") or data[dt].get("doc_version")
            if v:
                out.append({"doc_type": dt, "doc_version": str(v), "accepted_at": accepted_at})

    return out or fallback


def _auth_login(client: TestClient, email: str) -> Tuple[str, str]:
    r = client.post("/auth/request", json={"email": email})
    assert r.status_code == 200, r.text
    j = r.json()

    # request liefert i.d.R. challenge_id, wir akzeptieren auch challengeId (nur fürs Lesen)
    challenge_id = j.get("challenge_id") or j.get("challengeId")
    dev_otp = j.get("dev_otp") or j.get("otp") or j.get("devOtp")
    assert challenge_id, j
    assert dev_otp, j

    consents = _fetch_consents_for_verify(client)

    # /auth/verify Schema ist strikt: challenge_id + consents[*].doc_type/doc_version/accepted_at
    payload = {"challenge_id": challenge_id, "otp": dev_otp, "email": email, "consents": consents}
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

    r3 = client.post(
        "/sale/transfer/redeem",
        json={"transfer_token": token},
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert r3.status_code in (409, 410), r3.text

    rs = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_a}"})
    assert rs.status_code == 200, rs.text

    rs2 = client.get(f"/sale/transfer/status/{tid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert rs2.status_code == 200, rs2.text


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


def test_sale_transfer_status_admin_can_read(monkeypatch: pytest.MonkeyPatch, tmp_path):
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
    assert rs.status_code == 200, rs.text
