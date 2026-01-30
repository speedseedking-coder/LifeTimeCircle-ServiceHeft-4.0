from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.auth.crypto import token_hash as token_hash_fn
from app.auth.rbac import AuthContext, require_roles
from app.auth.storage import db, init_db, insert_session, upsert_user


# ---------- RBAC Unit Tests (sync, ohne pytest-asyncio) ----------

def test_require_roles_allows_user_roles():
    dep = require_roles("user", "vip", "dealer", "admin")
    for role in ["user", "vip", "dealer", "admin"]:
        ctx = AuthContext(user_id="u-1", role=role)
        out = dep(user=ctx)  # type: ignore[arg-type]
        assert out == ctx


def test_require_roles_denies_public_and_moderator():
    dep = require_roles("user", "vip", "dealer", "admin")
    for role in ["public", "moderator", "unknown"]:
        ctx = AuthContext(user_id="u-1", role=role)
        with pytest.raises(HTTPException) as exc:
            dep(user=ctx)  # type: ignore[arg-type]
        assert exc.value.status_code == 403


# ---------- API Tests (minimaler Nachweis: 401 + denied) ----------

TEST_SECRET = "x" * 40  # garantiert >= 32 Zeichen


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

    # Cache-clear (falls vorhanden)
    try:
        from app.core import config as _cfg  # type: ignore
        if hasattr(_cfg.get_settings, "cache_clear"):
            _cfg.get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass

    return db_path


def _make_token_for_role(db_path: str, role: str) -> str:
    secret = os.getenv("LTC_SECRET_KEY", TEST_SECRET)
    init_db(db_path)

    user_id = str(uuid.uuid4())
    email_hmac = "hmac_" + uuid.uuid4().hex  # unique, keine PII
    created_at = _iso(_utc_now())

    raw_token = "t_" + uuid.uuid4().hex
    token_hash = token_hash_fn(secret, raw_token)

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


@pytest.fixture()
def api_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _ensure_env(monkeypatch, tmp_path)
    from app.main import create_app  # import NACH env-set
    app = create_app()
    return TestClient(app)


def _find_masterclipboard_routes(app) -> list[APIRoute]:
    routes: list[APIRoute] = []
    for r in getattr(app, "routes", []):
        if not isinstance(r, APIRoute):
            continue
        p = (r.path or "").lower()
        name = (r.name or "").lower()
        if "masterclipboard" in p or "masterclipboard" in name:
            routes.append(r)
    return routes


def _pick_route(routes: list[APIRoute]) -> APIRoute:
    # bevorzugt GET ohne Path-Params; sonst erster Treffer
    for r in routes:
        if r.path and "{" not in r.path and (r.methods and "GET" in r.methods):
            return r
    return routes[0]


def _render_path(path_template: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path_template)


def _build_query_for_required_params(route: APIRoute) -> Dict[str, str]:
    q: Dict[str, str] = {}
    dep = route.dependant
    for qp in getattr(dep, "query_params", []) or []:
        if bool(getattr(qp, "required", False)):
            name = getattr(qp, "name", None)
            if name:
                q[name] = "1"
    return q


def _call_route(client: TestClient, route: APIRoute, *, token: Optional[str]) -> Any:
    method = "GET" if (route.methods and "GET" in route.methods) else sorted(route.methods or {"GET"})[0]
    path = _render_path(route.path)
    query = _build_query_for_required_params(route)

    idem = uuid.uuid4().hex
    headers: Dict[str, str] = {
        "Idempotency-Key": idem,
        "X-Idempotency-Key": idem,
        "X-Request-Id": uuid.uuid4().hex,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if method == "GET":
        return client.get(path, params=query, headers=headers)

    if method == "POST":
        return client.post(path, params=query, headers=headers, json={})
    if method == "PUT":
        return client.put(path, params=query, headers=headers, json={})
    if method == "PATCH":
        return client.patch(path, params=query, headers=headers, json={})
    if method == "DELETE":
        return client.delete(path, params=query, headers=headers)

    return client.request(method, path, params=query, headers=headers, json={})


def test_masterclipboard_requires_auth_401(api_client: TestClient):
    routes = _find_masterclipboard_routes(api_client.app)
    assert routes, "Keine Masterclipboard-Routen gefunden."

    route = _pick_route(routes)
    r = _call_route(api_client, route, token=None)
    assert r.status_code == 401, f"{route.methods} {route.path} -> {r.status_code} {r.text}"


def test_masterclipboard_denies_moderator(api_client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = _ensure_env(monkeypatch, tmp_path)
    moderator_token = _make_token_for_role(db_path, "moderator")

    # Token sanity: muss existieren (200 oder 403 – je nach Policy), aber nicht 401
    me = api_client.get("/auth/me", headers={"Authorization": f"Bearer {moderator_token}"})
    assert me.status_code in (200, 403), f"/auth/me -> {me.status_code} {me.text}"

    routes = _find_masterclipboard_routes(api_client.app)
    assert routes, "Keine Masterclipboard-Routen gefunden."

    route = _pick_route(routes)
    r = _call_route(api_client, route, token=moderator_token)

    # denied darf 401 oder 403 sein (je Umsetzung)
    assert r.status_code in (401, 403), f"{route.methods} {route.path} -> {r.status_code} {r.text}"


def test_auth_me_is_401_without_token_and_200_with_user(api_client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = _ensure_env(monkeypatch, tmp_path)
    user_token = _make_token_for_role(db_path, "user")

    r1 = api_client.get("/auth/me")
    assert r1.status_code == 401

    r2 = api_client.get("/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert r2.status_code == 200, f"/auth/me (user) -> {r2.status_code} {r2.text}"
