# server/tests/test_rbac_moderator_blog_only.py
from __future__ import annotations

from typing import Any

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


def _has_forbid_moderator(route: APIRoute) -> bool:
    names: set[str] = set()

    # dependencies via dependant
    try:
        for dep in getattr(route, "dependant", None).dependencies:  # type: ignore[union-attr]
            call = getattr(dep, "call", None)
            if call is None:
                continue
            names.add(getattr(call, "__name__", str(call)))
    except Exception:
        pass

    # dependencies via route.dependencies
    try:
        for dep in (route.dependencies or []):
            call = getattr(dep, "dependency", None)
            if call is None:
                continue
            names.add(getattr(call, "__name__", str(call)))
    except Exception:
        pass

    return "forbid_moderator" in names


def _is_allowed_path(path: str) -> bool:
    """
    Allowed = darf OHNE forbid_moderator existieren.

    - Auth muss für jede Rolle funktionieren (Login/Verify/Me)
    - Public-QR ist öffentlich
    - Consent-Contract Discovery ist öffentlich: /consent/current
    - OpenAPI/Docs sind Framework-Routen
    - Blog/News (falls vorhanden) darf Moderator sehen
    """
    if not path:
        return True

    # framework
    if path in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"):
        return True

    # auth endpoints (public/login + authed me/logout etc.)
    if path.startswith("/auth"):
        return True

    # public qr + ggf. blog/news
    if path.startswith("/public/qr"):
        return True
    if path.startswith("/public/blog") or path.startswith("/public/news"):
        return True

    # consent discovery must be public
    if path == "/consent/current":
        return True

    return False


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
