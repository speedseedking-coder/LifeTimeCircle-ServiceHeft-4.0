from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Iterable, Tuple

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

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

# SoT: Moderator darf nur Blog/News inkl. redaktioneller CMS-Pfade.
ALLOWED_PREFIXES = ("/news", "/blog", "/cms/blog", "/cms/news")


def _make_app():
    from app.main import create_app  # type: ignore

    return create_app()


def _apiroutes(app) -> Iterable[APIRoute]:
    for r in app.routes:
        if isinstance(r, APIRoute):
            yield r


def _replace_path_params(path: str) -> str:
    return re.sub(r"\{[^/}]+\}", "test", path)


def _pick_allowed_route(app) -> Tuple[str, str]:
    candidates = [r for r in _apiroutes(app) if any(r.path.startswith(p) for p in ALLOWED_PREFIXES)]

    if not candidates:
        all_paths = sorted({r.path for r in _apiroutes(app)})
        pytest.skip(
            "Blog/News Router noch nicht implementiert (keine /news oder /blog Routes). "
            "Sobald Blog/News vorhanden ist, wird dieser Test automatisch aktiv.\n"
            "Vorhandene Paths (Auszug):\n- " + "\n- ".join(all_paths[:140])
        )

    def score(r: APIRoute) -> Tuple[int, int]:
        has_params = 1 if "{" in r.path else 0
        has_get = 0 if (r.methods and "GET" in r.methods) else 1
        return (has_get, has_params)

    r = sorted(candidates, key=score)[0]
    methods = sorted(r.methods or [])
    method = "GET" if "GET" in methods else (methods[0] if methods else "GET")
    return method, _replace_path_params(r.path)


def _request_follow_redirects(client: TestClient, method: str, path: str):
    res = client.request(method, path)
    if res.status_code in (307, 308) and "location" in res.headers:
        res = client.request(method, res.headers["location"])
    return res


def _walk_dependant(dep: Dependant) -> Iterable[Dependant]:
    yield dep
    for child in getattr(dep, "dependencies", []) or []:
        yield from _walk_dependant(child)


def _override_actor_deps_everywhere(app, actor) -> None:
    seen = set()

    for r in _apiroutes(app):
        for dep in r.dependant.dependencies:
            for node in _walk_dependant(dep):
                call = getattr(node, "call", None)
                if call is None or call in seen:
                    continue
                seen.add(call)
                name = getattr(call, "__name__", "")
                if name in ACTOR_DEP_NAMES:
                    app.dependency_overrides[call] = (lambda a=actor: a)


def test_moderator_can_access_blog_or_news() -> None:
    """
    SoT: MODERATOR darf nur Blog/News.

    Sobald /blog oder /news Routes existieren:
      - Moderator darf dort nicht durch Auth/RBAC geblockt werden (nicht 401/403).
    """
    app = _make_app()
    actor = SimpleNamespace(uid="test_mod", role="moderator", roles=["moderator"])
    _override_actor_deps_everywhere(app, actor)

    client = TestClient(app)

    method, path = _pick_allowed_route(app)
    res = _request_follow_redirects(client, method, path)

    assert res.status_code not in (401, 403), f"{method} {path} -> {res.status_code}: {res.text}"
