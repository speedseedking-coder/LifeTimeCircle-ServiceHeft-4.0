import importlib
import os
import uuid
from typing import Callable, Iterable, Set, Tuple

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


class ActorStub(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e


def _make_app():
    os.makedirs("data", exist_ok=True)  # CI/Runner/Local safety
    mod = importlib.import_module("app.main")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    raise RuntimeError("Konnte FastAPI App nicht finden: erwartet app.main.create_app() oder app.main.app")


def _iter_dependant_calls(dependant) -> Iterable[Callable]:
    stack = [dependant]
    seen_ids: Set[int] = set()
    while stack:
        d = stack.pop()
        if d is None:
            continue
        did = id(d)
        if did in seen_ids:
            continue
        seen_ids.add(did)

        call = getattr(d, "call", None)
        if callable(call):
            yield call

        deps = getattr(d, "dependencies", None)
        if deps:
            stack.extend(list(deps))


def _looks_like_actor_provider(fn: Callable) -> bool:
    name = (getattr(fn, "__name__", "") or "").lower()
    mod = (getattr(fn, "__module__", "") or "").lower()

    if "actor" in name or "actor" in mod:
        return True
    if name in {"get_current_user", "require_user", "current_user", "get_user"}:
        return True
    if "principal" in name or "principal" in mod:
        return True
    if "current" in name and ("user" in name or "session" in name or "principal" in name):
        return True
    return False


def _override_actor(app, role: str) -> Tuple[int, Set[str]]:
    actor = ActorStub(
        role=role,
        user_id="test-user",
        subject="test-user",
        email="test@example.com",
    )

    overridden: Set[Callable] = set()
    overridden_names: Set[str] = set()

    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        if not (r.path or "").startswith("/documents"):
            continue

        for fn in _iter_dependant_calls(r.dependant):
            if _looks_like_actor_provider(fn):
                app.dependency_overrides[fn] = lambda a=actor: a
                overridden.add(fn)
                overridden_names.add(f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__name__', '?')}")

    if not overridden:
        for mp in ["app.auth.deps", "app.deps", "app.auth", "app.security"]:
            try:
                m = importlib.import_module(mp)
            except ModuleNotFoundError:
                continue
            for attr in dir(m):
                fn = getattr(m, attr, None)
                if callable(fn) and _looks_like_actor_provider(fn):
                    app.dependency_overrides[fn] = lambda a=actor: a
                    overridden.add(fn)
                    overridden_names.add(f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__name__', '?')}")

    if not overridden:
        raise RuntimeError("Konnte keine Actor-Provider-Dependency zum Überschreiben finden (siehe /documents dependencies).")

    return (len(overridden), overridden_names)


@pytest.fixture()
def client_base(monkeypatch):
    monkeypatch.setenv("LTC_SECRET_KEY", "dev_test_secret_key_32_chars_minimum__OK")
    return _make_app()


@pytest.mark.parametrize("role", ["user", "vip", "dealer", "moderator"])
def test_documents_quarantine_admin_endpoints_forbidden_for_non_admin_roles(client_base, role):
    app = client_base
    _override_actor(app, role)

    doc_id = str(uuid.uuid4())

    with TestClient(app) as c:
        assert c.get("/documents/admin/quarantine").status_code == 403
        assert c.post(f"/documents/{doc_id}/approve").status_code == 403
        assert c.post(f"/documents/{doc_id}/reject").status_code == 403


def test_documents_quarantine_requires_actor_unauthenticated_is_401(client_base):
    app = client_base
    doc_id = str(uuid.uuid4())

    with TestClient(app) as c:
        assert c.get("/documents/admin/quarantine").status_code == 401
        assert c.post(f"/documents/{doc_id}/approve").status_code == 401
        assert c.post(f"/documents/{doc_id}/reject").status_code == 401


def test_moderator_forbidden_on_documents_read_routes(client_base):
    app = client_base
    _override_actor(app, "moderator")

    doc_id = str(uuid.uuid4())

    with TestClient(app) as c:
        assert c.get(f"/documents/{doc_id}").status_code == 403
        assert c.get(f"/documents/{doc_id}/download").status_code == 403
