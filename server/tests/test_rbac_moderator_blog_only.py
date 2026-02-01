from fastapi.routing import APIRoute

from app.guards import forbid_moderator


ALLOW_PREFIXES = (
    "/news",
    "/blog",
    "/admin/news",
    "/admin/blog",
    "/public",
    "/qr",
    "/auth",
    "/docs",
    "/openapi",
    "/redoc",
)


def _is_allowed_path(path: str) -> bool:
    if not path:
        return True
    return any(path.startswith(p) for p in ALLOW_PREFIXES)


def _has_forbid_moderator(route: APIRoute) -> bool:
    deps = getattr(getattr(route, "dependant", None), "dependencies", None) or []
    return any(getattr(d, "call", None) is forbid_moderator for d in deps)


def test_auth_routes_not_blocked_by_forbid_moderator(client):
    auth_routes = [r for r in client.app.routes if isinstance(r, APIRoute) and str(r.path).startswith("/auth")]
    if not auth_routes:
        return
    blocked = [str(r.path) for r in auth_routes if _has_forbid_moderator(r)]
    assert not blocked, f"/auth Routen dürfen nicht forbid_moderator tragen: {blocked}"


def test_non_blog_routes_have_forbid_moderator_dependency(client):
    routes = [r for r in client.app.routes if isinstance(r, APIRoute)]
    assert routes, "Keine APIRoutes gefunden."

    missing_guard = []
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
