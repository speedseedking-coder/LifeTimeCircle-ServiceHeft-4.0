from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Iterable, Tuple

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


# Nur diese Dependency-Namen dürfen wir override'n (Actor-Quelle).
# Role-/Policy-Gates (forbid_moderator, require_roles, require_admin, ...) bleiben unangetastet.
ACTOR_DEP_NAMES = {
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


def _replace_path_params(path: str) -> str:
    # /x/{id}/y -> /x/test/y
    return re.sub(r"\{[^/}]+\}", "test", path)


def _pick_route(app, prefix: str) -> Tuple[str, str]:
    """
    Wählt eine existierende Route unter prefix.
    Bevorzugt: GET ohne Path-Params, sonst irgendeine GET/POST Route.
    """
    candidates = [r for r in _apiroutes(app) if r.path.startswith(prefix)]

    if not candidates:
        all_paths = sorted({r.path for r in _apiroutes(app)})
        raise AssertionError(
            f"Keine Routes unter prefix={prefix!r} gefunden.\n"
            f"Vorhandene Paths (Auszug):\n- " + "\n- ".join(all_paths[:120])
        )

    def score(r: APIRoute) -> Tuple[int, int]:
        has_params = 1 if "{" in r.path else 0
        has_get = 0 if (r.methods and "GET" in r.methods) else 1
        return (has_get, has_params)

    r = sorted(candidates, key=score)[0]
    methods = sorted(r.methods or [])
    method = "GET" if "GET" in methods else (methods[0] if methods else "GET")

    path = _replace_path_params(r.path)
    return method, path


def _request_follow_redirects(client: TestClient, method: str, path: str):
    res = client.request(method, path)
    if res.status_code in (307, 308) and "location" in res.headers:
        res = client.request(method, res.headers["location"])
    return res


def _override_actor_deps_everywhere(app, actor) -> None:
    """
    Robust: wir schauen in *alle* APIRoutes und override'n alle Depends(call),
    deren Callable-Name in ACTOR_DEP_NAMES liegt.
    """
    for r in _apiroutes(app):
        for dep in r.dependant.dependencies:
            call = dep.call
            name = getattr(call, "__name__", "")
            if name in ACTOR_DEP_NAMES:
                # default-arg bindet actor, damit lambda nicht late-bound ist
                app.dependency_overrides[call] = (lambda a=actor: a)


def _client_as_moderator() -> TestClient:
    app = _make_app()

    # Actor-Objekt mit typischen Feldern
    actor = SimpleNamespace(uid="test_mod", role="moderator", roles=["moderator"])

    _override_actor_deps_everywhere(app, actor)

    return TestClient(app)


def test_moderator_blocked_on_documents_routes() -> None:
    """
    SoT: Moderator nur Blog/News -> /documents/* muss 403 sein.
    """
    client = _client_as_moderator()
    app = client.app

    method, path = _pick_route(app, "/documents")
    res = _request_follow_redirects(client, method, path)

    assert res.status_code == 403, f"{method} {path} -> {res.status_code}: {res.text}"


def test_moderator_blocked_on_export_routes() -> None:
    """
    SoT: Moderator nur Blog/News -> /export/* muss 403 sein.
    """
    client = _client_as_moderator()
    app = client.app

    method, path = _pick_route(app, "/export")
    res = _request_follow_redirects(client, method, path)

    assert res.status_code == 403, f"{method} {path} -> {res.status_code}: {res.text}"


def test_moderator_blocked_on_admin_routes() -> None:
    """
    SoT: Moderator nur Blog/News -> /admin/* muss 403 sein.
    """
    client = _client_as_moderator()
    app = client.app

    method, path = _pick_route(app, "/admin")
    res = _request_follow_redirects(client, method, path)

    assert res.status_code == 403, f"{method} {path} -> {res.status_code}: {res.text}"