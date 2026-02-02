# server/scripts/rbac_route_audit.py
# Prüft, ob kritische Prefix-Routen forbid_moderator enthalten.
# Run: poetry run python .\scripts\rbac_route_audit.py

from __future__ import annotations

from fastapi.routing import APIRoute


def _dep_names(route: APIRoute) -> set[str]:
    names: set[str] = set()

    # Dependencies aus "dependant"
    try:
        for dep in getattr(route, "dependant", None).dependencies:  # type: ignore[union-attr]
            call = getattr(dep, "call", None)
            if call is None:
                continue
            names.add(getattr(call, "__name__", str(call)))
    except Exception:
        pass

    # Dependencies aus route.dependencies
    try:
        for dep in (route.dependencies or []):
            call = getattr(dep, "dependency", None)
            if call is None:
                continue
            names.add(getattr(call, "__name__", str(call)))
    except Exception:
        pass

    return names


def main() -> int:
    # Import erst hier, damit FastAPI App sauber lädt
    from app.main import app  # noqa

    required_prefixes = ("/admin", "/export", "/api/masterclipboard")

    # consent/current ist bewusst public discovery; nicht in die Moderator-Block-Liste zwingen
    exempt_paths = {"/consent/current"}

    missing: list[tuple[str, list[str]]] = []

    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue

        path = r.path

        if path in exempt_paths:
            continue

        if path.startswith(required_prefixes):
            deps = _dep_names(r)
            if "forbid_moderator" not in deps:
                missing.append((path, sorted(deps)))

    if missing:
        print("RBAC CHECK FAILED: forbid_moderator fehlt auf folgenden Routen:")
        for path, deps in missing:
            print(f"- {path}  deps={deps}")
        return 1

    print("OK: Alle kritischen Prefix-Routen enthalten forbid_moderator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
