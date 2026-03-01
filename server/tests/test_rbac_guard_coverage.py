# server/tests/test_rbac_guard_coverage.py
from __future__ import annotations

from typing import List, Set, Tuple

from fastapi.routing import APIRoute
from fastapi.dependencies.models import Dependant

from app.main import create_app

# Gates, die als "Auth vorhanden" zählen (deny-by-default)
AUTH_GATES: Set[str] = {
    # project-typisch
    "get_actor",
    "require_roles",
    "require_role",
    "require_moderator",
    "forbid_moderator",
    # fallback (falls im Projekt vorhanden)
    "require_admin",
    "require_superadmin",
    "rbac_guard",
    "HTTPBearer",
}

# Gates, die als "Moderator geblockt" zählen (außer Allowlist)
MODERATOR_BLOCK_GATES: Set[str] = {
    "forbid_moderator",
    "require_roles",
    "require_role",
    "require_admin",
    "require_superadmin",
    "rbac_guard",
}


def _get_app():
    return create_app()


def _is_public_path(path: str) -> bool:
    """
    Public = ohne Actor/Auth erreichbar.
    Wichtig: /blog* und /news* sind public & im MODERATOR-Allowlist.
    """
    if path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
        return True
    if path == "/health" or path.startswith("/health/"):
        return True
    if path == "/auth" or path.startswith("/auth/"):
        return True
    if path == "/public" or path.startswith("/public/"):
        return True
    if path == "/blog" or path.startswith("/blog/"):
        return True
    if path == "/news" or path.startswith("/news/"):
        return True
    return False


def _is_moderator_allowed_path(path: str) -> bool:
    """
    MODERATOR-Allowlist (SoT):
    /auth/*, /blog/*, /news/*, /cms/blog/*, /cms/news/*
    """
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
    # docs/openapi sind ohnehin public
    if path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
        return True
    return False


def _collect_dep_names(route: APIRoute) -> Set[str]:
    """
    Sammelt __name__ der Dependencies (rekursiv).
    """
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

    # Security-Reqs (wenn genutzt)
    try:
        for req in route.dependant.security_requirements:  # type: ignore[attr-defined]
            scheme = getattr(req, "security_scheme", None)
            if scheme is None:
                continue
            cls = getattr(scheme, "__class__", None)
            if cls is not None:
                names.add(getattr(cls, "__name__", ""))
            scheme_name = getattr(scheme, "scheme_name", None)
            if scheme_name:
                names.add(str(scheme_name))
    except Exception:
        pass

    return {n for n in names if n}


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

        # Public darf ohne Auth sein
        if _is_public_path(path):
            continue

        dep_names = _collect_dep_names(r)

        # 1) Auth vorhanden?
        if dep_names.isdisjoint(AUTH_GATES):
            for m in sorted(r.methods or []):
                missing.append((m, path, "Auth-Gate fehlt (z.B. forbid_moderator/get_actor/require_roles/...)"))

        # 2) Moderator block (außer Allowlist)
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
