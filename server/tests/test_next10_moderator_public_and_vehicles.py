# server/tests/test_next10_moderator_public_and_vehicles.py
from __future__ import annotations

import re
import uuid
from types import SimpleNamespace
from typing import Iterable, List, Set, Tuple

from fastapi import HTTPException
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


# Sehr defensiv: wir überschreiben nur Actor/User/Principal-Provider, NICHT die RBAC-Guards selbst.
ACTOR_PROVIDER_NAMES: Set[str] = {
    "get_actor",
    "require_actor",
    "get_current_actor",
    "get_current_user",
    "require_user",
    "get_principal",
    "require_principal",
    "get_session_actor",
    "require_session_actor",
}


def _make_app():
    from app.main import create_app  # type: ignore

    return create_app()


def _apiroutes(app) -> Iterable[APIRoute]:
    for r in app.routes:
        if isinstance(r, APIRoute):
            yield r


def _walk_dependant(dep: Dependant) -> Iterable[Dependant]:
    yield dep
    for d in getattr(dep, "dependencies", []) or []:
        yield from _walk_dependant(d)


def _looks_like_actor_provider(name: str) -> bool:
    # niemals Guards/Role-Gates überschreiben
    if name in {"forbid_moderator", "require_roles", "require_any_role", "require_role"}:
        return False
    if name in ACTOR_PROVIDER_NAMES:
        return True
    if ("actor" in name or "user" in name or "principal" in name) and (
        name.startswith("get_") or name.startswith("require_")
    ):
        return True
    return False


def _override_actor_deps_everywhere(app, actor) -> None:
    """
    Override nur der Actor-Quelle (dependency overrides), nicht der Guards selbst.
    """
    seen = set()
    for r in _apiroutes(app):
        for dep in r.dependant.dependencies:
            for node in _walk_dependant(dep):
                call = getattr(node, "call", None)
                if call is None or call in seen:
                    continue
                seen.add(call)
                name = getattr(call, "__name__", "")
                if _looks_like_actor_provider(name):
                    app.dependency_overrides[call] = (lambda a=actor: a)


def _pick_method(methods: Set[str]) -> str:
    for m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        if m in methods:
            return m
    return sorted(methods)[0] if methods else "GET"


def _materialize_path(r: APIRoute) -> str:
    """
    Ersetze Path-Params typ-sicher, um 422 durch UUID/int zu vermeiden.
    """
    path = r.path

    for f in getattr(r.dependant, "path_params", []) or []:
        t = getattr(f, "type_", None)
        if t is int:
            v = "1"
        elif t is uuid.UUID:
            v = "00000000-0000-0000-0000-000000000000"
        else:
            v = "test"
        path = path.replace("{" + f.name + "}", v)

    path = re.sub(r"\{[^/}]+\}", "test", path)
    return path


def _request_follow_redirects(client: TestClient, method: str, path: str):
    kwargs = {}
    if method in {"POST", "PUT", "PATCH"}:
        # Minimal/invalid, um Side-Effects zu vermeiden;
        kwargs["json"] = {}

    res = client.request(method, path, **kwargs)

    if res.status_code in (307, 308) and "location" in res.headers:
        res = client.request(method, res.headers["location"], **kwargs)

    return res


def _vehicles_sample_routes(app) -> List[APIRoute]:
    vehicles_routes = sorted(
        [r for r in _apiroutes(app) if r.path.startswith("/vehicles")],
        key=lambda r: (r.path, sorted(r.methods or [])),
    )

    if not vehicles_routes:
        raise AssertionError("Keine /vehicles-Routen registriert")

    root_route = next((r for r in vehicles_routes if r.path in {"/vehicles", "/vehicles/"}), None)
    if root_route is None:
        raise AssertionError("Route /vehicles ist nicht registriert")

    sample = [root_route]
    extra = next((r for r in vehicles_routes if r.path not in {"/vehicles", "/vehicles/"}), None)
    if extra is not None:
        sample.append(extra)

    return sample


def _assert_consent_required_payload(res) -> None:
    """
    Akzeptiert beide gängigen Shapes:
    - {"detail": "consent_required"}
    - {"detail": {"code": "consent_required", ...}}
    """
    if not (res.headers.get("content-type", "").startswith("application/json")):
        raise AssertionError(f"Expected JSON response, got content-type={res.headers.get('content-type')!r}")

    payload = res.json()
    if not isinstance(payload, dict):
        raise AssertionError(f"Expected dict payload, got: {payload!r}")

    detail = payload.get("detail")
    if detail == "consent_required":
        return
    if isinstance(detail, dict) and detail.get("code") == "consent_required":
        return

    raise AssertionError(f"Expected consent_required in detail, got payload={payload!r}")


def test_moderator_is_403_on_public_site_qr_and_vehicles() -> None:
    """
    Contract (SoT):
    - Moderator ist strikt nur Blog/News -> /public/* und /vehicles/* müssen 403 sein.
    """
    app = _make_app()
    actor = SimpleNamespace(uid="test_mod", user_id="test_mod", role="moderator", roles=["moderator"])
    _override_actor_deps_everywhere(app, actor)

    client = TestClient(app)

    checks: List[Tuple[str, str]] = [
        ("GET", "/public/site"),
        ("GET", "/public/qr/test-token"),
    ]

    for r in _vehicles_sample_routes(app):
        method = _pick_method(set(r.methods or []))
        path = _materialize_path(r)
        checks.append((method, path))

    failures: List[str] = []
    for method, path in checks:
        res = _request_follow_redirects(client, method, path)

        if res.status_code != 403:
            txt = (res.text or "").replace("\r", "")[:220]
            failures.append(f"- {method} {path} -> {res.status_code}: {txt}")

    if failures:
        raise AssertionError("Moderator ist nicht fail-closed (erwartet 403):\n" + "\n".join(failures))


def test_authenticated_without_consent_gets_403_consent_required_on_vehicles(monkeypatch) -> None:
    """
    Contract (SoT):
    - Authenticated user ohne Consent bekommt auf /vehicles/*:
      403 + consent_required Signal.
    """
    app = _make_app()
    actor = SimpleNamespace(uid="test_user", user_id="test_user", role="user", roles=["user"])
    _override_actor_deps_everywhere(app, actor)

    import app.routers.vehicles as vehicles_mod  # type: ignore

    def _deny_due_to_missing_consent(*_a, **_kw):
        raise HTTPException(status_code=403, detail="consent_required")

    monkeypatch.setattr(vehicles_mod, "require_consent", _deny_due_to_missing_consent, raising=True)

    client = TestClient(app)

    for r in _vehicles_sample_routes(app):
        method = _pick_method(set(r.methods or []))
        path = _materialize_path(r)
        res = _request_follow_redirects(client, method, path)

        if res.status_code != 403:
            raise AssertionError(f"{method} {path} -> {res.status_code}: {res.text[:220]}")

        _assert_consent_required_payload(res)


def test_happy_path_with_consent_reaches_vehicles_200(monkeypatch) -> None:
    """
    Minimal Happy Path:
    - Nicht-Moderator + Consent ok -> mind. GET /vehicles => 200 (typisch []).
    """
    app = _make_app()
    actor = SimpleNamespace(uid="ok_user", user_id="ok_user", role="user", roles=["user"])
    _override_actor_deps_everywhere(app, actor)

    import app.routers.vehicles as vehicles_mod  # type: ignore

    monkeypatch.setattr(vehicles_mod, "require_consent", lambda *_a, **_kw: None, raising=True)

    client = TestClient(app)
    res = client.get("/vehicles")

    assert res.status_code == 200, f"GET /vehicles -> {res.status_code}: {res.text[:220]}"
    assert res.headers.get("content-type", "").startswith("application/json")