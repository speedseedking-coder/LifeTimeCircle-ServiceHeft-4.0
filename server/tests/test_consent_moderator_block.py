from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient


def _make_app():
    # create_app ist bei euch etabliert (siehe Guard-Coverage-Test)
    from app.main import create_app  # type: ignore

    return create_app()


def _try_import_dep():
    """
    Versucht get_actor/require_actor aus den üblichen Modulen zu laden.
    Wir override'n nur die Actor-Quelle, nicht forbid_moderator.
    """
    candidates = ("app.auth.deps", "app.deps")
    last_err: Exception | None = None

    for mod in candidates:
        try:
            m = __import__(mod, fromlist=["get_actor", "require_actor"])
            get_actor = getattr(m, "get_actor", None)
            require_actor = getattr(m, "require_actor", None)
            if get_actor is None and require_actor is None:
                continue
            return get_actor, require_actor
        except Exception as e:
            last_err = e

    raise ImportError(
        "Konnte weder get_actor noch require_actor importieren. "
        "Bitte `rg -n \"def (get_actor|require_actor)\" server/app -S` ausführen."
    ) from last_err


def test_moderator_gets_403_on_consent_current() -> None:
    """
    SoT: MODERATOR darf nur Blog/News.
    Consent ist kein Blog/News -> Moderator muss geblockt werden (403).
    """
    app = _make_app()

    # Actor-Objekt mit typischen Feldern
    actor = SimpleNamespace(uid="test_mod", role="moderator", roles=["moderator"])

    get_actor, require_actor = _try_import_dep()

    if get_actor is not None:
        app.dependency_overrides[get_actor] = lambda: actor
    if require_actor is not None:
        app.dependency_overrides[require_actor] = lambda: actor

    client = TestClient(app)
    res = client.get("/consent/current")

    assert res.status_code == 403, res.text