# server/tests/test_rbac_guard_coverage.py
from __future__ import annotations

import functools
from typing import Callable, Iterable, List, Set, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute


def _get_app() -> FastAPI:
    """
    Projektkonvention: app.main stellt create_app() bereit.
    Fallback: app-Instanz.
    """
    try:
        from app.main import create_app  # type: ignore

        return create_app()
    except Exception:
        from app.main import app  # type: ignore

        return app


PUBLIC_EXACT = {
    "/",
    "/health",
    "/healthz",
    "/openapi.json",
}

PUBLIC_PREFIXES = (
    "/auth",
    "/public",
    "/public-qr",
    "/docs",
    "/redoc",
)

MODERATOR_ALLOWED_PREFIXES = (
    "/blog",
    "/news",
)

# Auth-/Role-Gates, die als "auth vorhanden" zählen.
# Wichtig: forbid_moderator zählt als Auth-Gate, weil es einen Actor braucht (Auth implizit).
AUTH_GATES: Set[str] = {
    "get_actor",
    "require_actor",
    "require_roles",
    "require_admin",
    "require_superadmin",
    "forbid_moderator",
}

# Moderator-Block ist erfüllt, wenn forbid_moderator vorhanden ist ODER ein Role-Gate greift,
# das Moderator implizit ausschließt (admin/superadmin/require_roles).
MODERATOR_BLOCK_GATES: Set[str] = {
    "forbid_moderator",
    "require_roles",
    "require_admin",
    "require_superadmin",
}


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    for p in PUBLIC_PREFIXES:
        if path == p or path.startswith(p + "/"):
            return True
    return False


def _is_moderator_allowed_path(path: str) -> bool:
    for p in MODERATOR_ALLOWED_PREFIXES:
        if path == p or path.startswith(p + "/"):
            return True
    return False


def _unwrap_callable(c: Callable) -> Callable:
    if isinstance(c, functools.partial):
        c = c.func  # type: ignore[assignment]
    while hasattr(c, "__wrapped__"):
        c = getattr(c, "__wrapped__")  # type: ignore[assignment]
    return c


def _callable_name(c: Callable) -> str:
    c = _unwrap_callable(c)
    return getattr(c, "__name__", c.__class__.__name__)


def _iter_dependency_calls(route: APIRoute) -> Iterable[Callable]:
    """
    Traversiert route.dependant.dependencies rekursiv.
    """
    stack = list(getattr(route, "dependant").dependencies)
    while stack:
        dep = stack.pop()
        call = getattr(dep, "call", None)
        if callable(call):
            yield call
        nested = getattr(dep, "dependencies", None)
        if nested:
            stack.extend(list(nested))


def _collect_dep_names(route: APIRoute) -> Set[str]:
    return {_callable_name(c) for c in _iter_dependency_calls(route)}


def test_rbac_guard_coverage_deny_by_default() -> None:
    """
    Security FIX: deny-by-default + least privilege, serverseitig enforced.

    Erwartung:
      - Nicht-public Routes müssen irgendein Auth-/Role-Gate haben.
      - Moderator darf nur Blog/News: überall sonst forbid_moderator ODER Role-Gate, das Moderator ausschließt.
    """
    app = _get_app()

    missing: List[Tuple[str, str, str]] = []

    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue

        path = r.path
        if _is_public_path(path):
            continue

        dep_names = _collect_dep_names(r)

        # 1) Auth vorhanden?
        if dep_names.isdisjoint(AUTH_GATES):
            for m in sorted(r.methods or []):
                missing.append((m, path, "Auth-Gate fehlt (z.B. forbid_moderator/get_actor/require_roles/...)"))

        # 2) Moderator block (außer Blog/News)
        if not _is_moderator_allowed_path(path):
            if dep_names.isdisjoint(MODERATOR_BLOCK_GATES):
                for m in sorted(r.methods or []):
                    missing.append((m, path, "Moderator-Block fehlt (forbid_moderator oder Role-Gate)"))

    if missing:
        missing_sorted = sorted(set(missing))
        lines = ["RBAC Guard-Coverage fehlt (deny-by-default verletzt):"]
        for method, path, reason in missing_sorted:
            lines.append(f"- {method} {path}: {reason}")
        raise AssertionError("\n".join(lines))