import os

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("LTC_SECRET_KEY", "dev_test_secret_key_32_chars_minimum__OK")


class ActorStub(dict):
    def __getattr__(self, item):
        return self.get(item)


@pytest.fixture()
def mem_engine():
    return create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


@pytest.fixture()
def mem_db(mem_engine):
    SessionLocal = sessionmaker(bind=mem_engine, autocommit=False, autoflush=False, future=True)

    from app.db.base import Base  # type: ignore
    from app.models.vehicle import Vehicle  # noqa: F401

    Base.metadata.create_all(bind=mem_engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _wire_app(mem_db, actor: ActorStub, monkeypatch=None, bypass_consent: bool = False):
    from app.routers import vehicles as vehicles_mod  # type: ignore

    app = FastAPI()
    app.include_router(vehicles_mod.router)

    def _get_db():
        yield mem_db

    app.dependency_overrides[vehicles_mod.get_db] = _get_db  # type: ignore
    app.dependency_overrides[vehicles_mod.require_actor] = lambda: actor  # type: ignore

    if bypass_consent and monkeypatch is not None:
        monkeypatch.setattr(vehicles_mod, "require_consent", lambda db, actor: None, raising=True)

    return app, vehicles_mod


def test_table_creation_via_init_db(monkeypatch, mem_engine):
    import app.db.session as session_mod  # type: ignore

    SessionLocal = sessionmaker(bind=mem_engine, autocommit=False, autoflush=False, future=True)

    monkeypatch.setattr(session_mod, "_ENGINE", None, raising=False)
    monkeypatch.setattr(session_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(session_mod, "create_engine", lambda *a, **k: mem_engine, raising=False)
    monkeypatch.setattr(session_mod, "sessionmaker", lambda *a, **k: SessionLocal, raising=False)

    session_mod.init_db()

    insp = inspect(mem_engine)
    assert insp.has_table("vehicles"), "vehicles table fehlt (Model nicht registriert in init_db())"


def test_consent_required_not_swallowed(mem_db, monkeypatch):
    actor = ActorStub(user_id="u1", role="user")
    app, vehicles_mod = _wire_app(mem_db, actor, monkeypatch=monkeypatch, bypass_consent=False)

    def _raise_consent(*args, **kwargs):
        raise HTTPException(status_code=403, detail={"code": "consent_required"})

    monkeypatch.setattr(vehicles_mod, "require_consent", _raise_consent, raising=True)

    client = TestClient(app)
    r = client.get("/vehicles")
    assert r.status_code == 403
    detail = r.json().get("detail")
    assert isinstance(detail, dict)
    assert detail.get("code") == "consent_required"


def test_vin_masking(mem_db, monkeypatch):
    from app.models.vehicle import Vehicle  # type: ignore

    v = Vehicle(owner_user_id="u1", meta={"nickname": "X"})
    v.set_vin_from_raw("WVWZZZ1JZXW000001")
    mem_db.add(v)
    mem_db.commit()
    mem_db.refresh(v)

    actor = ActorStub(user_id="u1", role="user")
    app, _vehicles_mod = _wire_app(mem_db, actor, monkeypatch=monkeypatch, bypass_consent=True)
    client = TestClient(app)

    r = client.get(f"/vehicles/{v.public_id}")
    assert r.status_code == 200
    payload = r.json()

    assert "vin_masked" in payload
    assert "WVWZZZ1JZXW000001" not in payload["vin_masked"]
    assert payload["vin_masked"].startswith("WVW")
    assert payload["vin_masked"].endswith("0001")


def test_owner_object_level_protection(mem_db, monkeypatch):
    from app.models.vehicle import Vehicle  # type: ignore

    v = Vehicle(owner_user_id="u_owner")
    v.set_vin_from_raw("WVWZZZ1JZXW000001")
    mem_db.add(v)
    mem_db.commit()
    mem_db.refresh(v)

    actor_other = ActorStub(user_id="u_other", role="user")
    app, _vehicles_mod = _wire_app(mem_db, actor_other, monkeypatch=monkeypatch, bypass_consent=True)
    client = TestClient(app)

    r = client.get(f"/vehicles/{v.public_id}")
    assert r.status_code in (403, 404)


def test_moderator_blocked_on_vehicles(mem_db, monkeypatch):
    actor = ActorStub(user_id="m1", role="moderator")
    app, _vehicles_mod = _wire_app(mem_db, actor, monkeypatch=monkeypatch, bypass_consent=True)

    client = TestClient(app)
    r = client.get("/vehicles")
    assert r.status_code == 403
