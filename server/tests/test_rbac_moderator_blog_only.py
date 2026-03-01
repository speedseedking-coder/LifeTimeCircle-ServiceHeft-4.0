# server/tests/test_rbac_moderator_blog_only.py
from __future__ import annotations

from typing import Set

from fastapi.routing import APIRoute
from fastapi.dependencies.models import Dependant
from starlette.testclient import TestClient


def _is_allowed_path(path: str) -> bool:
    """
    MODERATOR-Allowlist (SoT):
    strikt nur /blog/*, /news/*, /cms/blog/* und /cms/news/* (+ /auth/* fuer Login/Token-Erneuerung).
    """
    if path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
        return True
    if path == "/auth" or path.startswith("/auth/"):
        return True
    if path == "/blog" or path.startswith("/blog/"):
        return True
    if path == "/news" or path.startswith("/news/"):
        return True
    if path == "/cms/blog" or path.startswith("/cms/blog/"):
        return True
    if path == "/cms/news" or path.startswith("/cms/news/"):
        return True
    return False


def _collect_dep_names(route: APIRoute) -> Set[str]:
    names: Set[str] = set()

    def walk(dep: Dependant | None) -> None:
        if dep is None:
            return
        call = getattr(dep, "call", None)
        if call is not None:
            n = getattr(call, "__name__", None)
            if n:
                names.add(str(n))
        for child in getattr(dep, "dependencies", []) or []:
            walk(child)

    walk(getattr(route, "dependant", None))
    return {n for n in names if n}


def _has_forbid_moderator(route: APIRoute) -> bool:
    return "forbid_moderator" in _collect_dep_names(route)


def test_non_blog_routes_have_forbid_moderator_dependency(client: TestClient) -> None:
    routes = [r for r in client.app.routes if isinstance(r, APIRoute)]
    assert routes, "Keine APIRoutes gefunden."

    missing_guard: list[str] = []
    saw_deny = False

    for r in routes:
        path = str(getattr(r, "path", ""))

        if _is_allowed_path(path):
            continue

        saw_deny = True
        if not _has_forbid_moderator(r):
            missing_guard.append(path)

    assert saw_deny, "Keine deny-Routen gefunden – Test nicht aussagekräftig."
    assert not missing_guard, f"forbid_moderator fehlt auf deny-Routen (Auszug): {missing_guard[:20]}"
