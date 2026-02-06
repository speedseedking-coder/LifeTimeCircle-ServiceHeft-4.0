from __future__ import annotations

import re
import uuid
from types import SimpleNamespace
from typing import Iterable, List, Set, Tuple

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


# MODERATOR darf nur Blog/News. Auth/Public müssen trotzdem funktionieren.
EXEMPT_PREFIXES = (
    "/health",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/public",  # z.B. /public/qr/*
    "/auth",    # login/otp/magic-link/me/logout/consent-flow
)

ALLOWED_PREFIXES = ("/blog", "/news")  # sobald vorhanden: Moderator darf hier rein


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
    # sehr defensiv: wir wollen nur "Actor/User/Principal" Provider overrriden,
    # nicht aber forbid_moderator / role checks selbst.
    if name in {"forbid_moderator", "require_roles", "require_any_role"}:
        return False
    if name in {
        "get_actor",
        "require_actor",
        "get_current_actor",
        "get_current_user",
        "require_user",
        "get_principal",
        "require_principal",
        "get_session_actor",
        "require_session_actor",
    }:
        return True
    if ("actor" in name or "user" in name or "principal" in name) and (
        name.startswith("get_") or name.startswith("require_")
    ):
        return True
    return False


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
                if _looks_like_actor_provider(name):
                    app.dependency_overrides[call] = (lambda a=actor: a)


def _pick_method(methods: Set[str]) -> str:
    for m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        if m in methods:
            return m
    return sorted(methods)[0] if methods else "GET"


def _materialize_path(r: APIRoute) -> str:
    # Ersetze Path-Params typ-sicher, damit wir nicht unnötig 422 wegen UUID/int bekommen.
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

    # fallback: alles, was noch übrig ist
    path = re.sub(r"\{[^/}]+\}", "test", path)
    return path


def _request_follow_redirects(client: TestClient, method: str, path: str):
    kwargs = {}
    if method in {"POST", "PUT", "PATCH"}:
        # absichtlich "invalid minimal", damit wir side-effects vermeiden;
        # wenn Moderator nicht geblockt ist, käme typischerweise 422 (=> Fail).
        kwargs["json"] = {}

    res = client.request(method, path, **kwargs)

    if res.status_code in (307, 308) and "location" in res.headers:
        res = client.request(method, res.headers["location"], **kwargs)

    return res


def test_moderator_blocked_everywhere_except_auth_public_and_blog_news() -> None:
    """
    SoT: MODERATOR strikt nur Blog/News; ansonsten geblockt.
    Runtime-Check: für jede Route außerhalb EXEMPT_PREFIXES und ALLOWED_PREFIXES muss 403 kommen.
    """
    app = _make_app()
    actor = SimpleNamespace(uid="test_mod", role="moderator", roles=["moderator"])
    _override_actor_deps_everywhere(app, actor)

    client = TestClient(app)

    failures: List[Tuple[str, str, int, str]] = []

    for r in sorted(_apiroutes(app), key=lambda x: (x.path, sorted(x.methods or []))):
        path = r.path

        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            continue
        if any(path.startswith(p) for p in ALLOWED_PREFIXES):
            # die "allowed" Seite wird separat geprüft (und ist bis zur Implementierung SKIP)
            continue

        methods = set(r.methods or [])
        method = _pick_method(methods)
        req_path = _materialize_path(r)

        res = _request_follow_redirects(client, method, req_path)

        if res.status_code != 403:
            txt = (res.text or "").replace("\r", "")[:220]
            failures.append((method, path, res.status_code, txt))

    if failures:
        lines = ["Moderator-Block Coverage verletzt (erwartet 403):"]
        for method, path, code, txt in failures:
            lines.append(f"- {method} {path} -> {code}: {txt}")
        raise AssertionError("\n".join(lines))