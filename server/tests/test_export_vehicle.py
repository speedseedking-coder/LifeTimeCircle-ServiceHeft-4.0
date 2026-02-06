import os
import datetime as dt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    DateTime,
    insert,
    update,
    select,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.routers import export_vehicle
from app.services.export_crypto import decrypt_json


@pytest.fixture()
def engine():
    # WICHTIG: TestClient nutzt Threads -> SQLite muss thread-übergreifend erlaubt sein
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    md = MetaData()
    vehicles = Table(
        "vehicles",
        md,
        Column("id", String, primary_key=True),
        Column("owner_id", String, nullable=True),
        Column("vin", String, nullable=True),
        Column("owner_email", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=True),
    )
    md.create_all(engine)

    # Seed
    with engine.begin() as conn:
        conn.execute(
            insert(vehicles).values(
                id="veh_1",
                owner_id="user_1",
                vin="WVWZZZ1JZXW000001",
                owner_email="private@example.com",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
        )

    return engine


@pytest.fixture()
def SessionLocal(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def app(SessionLocal, monkeypatch):
    monkeypatch.setenv("LTC_SECRET_KEY", "dev-only-change-me-please-change-me-32chars-XXXX")

    app = FastAPI()
    app.include_router(export_vehicle.router)

    # pro Request eigene Session (thread-safe für Tests)
    def override_get_db():
        with SessionLocal() as s:
            yield s

    actor_box = {"actor": {"role": "user", "user_id": "user_1"}}

    def override_get_actor():
        return actor_box["actor"]

    app.dependency_overrides[export_vehicle.get_db] = override_get_db
    app.dependency_overrides[export_vehicle.get_actor] = override_get_actor

    app.state._actor_box = actor_box
    app.state._SessionLocal = SessionLocal
    return app


@pytest.fixture()
def client(app):
    return TestClient(app)


def set_actor(app, *, role: str, user_id: str | None = None):
    actor = {"role": role}
    if user_id is not None:
        actor["user_id"] = user_id
    app.state._actor_box["actor"] = actor


def test_redacted_export_owner_allowed(app, client):
    set_actor(app, role="user", user_id="user_1")
    r = client.get("/export/vehicle/veh_1")
    assert r.status_code == 200
    body = r.json()
    data = body["data"]
    assert data["_redacted"] is True
    assert "owner_email" not in data
    assert "vin" not in data
    assert "vin_hmac" in data


def test_redacted_export_scope_denied(app, client):
    set_actor(app, role="user", user_id="user_2")
    r = client.get("/export/vehicle/veh_1")
    assert r.status_code == 403


def test_moderator_blocked(app, client):
    set_actor(app, role="moderator", user_id="mod_1")
    r = client.get("/export/vehicle/veh_1")
    assert r.status_code == 403
    r2 = client.post("/export/vehicle/veh_1/grant")
    assert r2.status_code == 403


def test_grant_and_full_one_time_token(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")

    g = client.post("/export/vehicle/veh_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    f1 = client.get("/export/vehicle/veh_1/full", headers={"X-Export-Token": tok})
    assert f1.status_code == 200
    ciphertext = f1.json()["ciphertext"]
    payload = decrypt_json(ciphertext)
    assert payload["target"] == "vehicle"
    assert payload["id"] == "veh_1"
    assert payload["vehicle"]["vin"] == "WVWZZZ1JZXW000001"
    assert payload["vehicle"]["owner_email"] == "private@example.com"

    # one-time -> zweites Mal muss scheitern
    f2 = client.get("/export/vehicle/veh_1/full", headers={"X-Export-Token": tok})
    assert f2.status_code == 403


def test_full_requires_token(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")
    r = client.get("/export/vehicle/veh_1/full")
    assert r.status_code == 400


def test_ttl_enforced_without_sleep(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")

    os.environ["LTC_EXPORT_TTL_SECONDS"] = "600"
    g = client.post("/export/vehicle/veh_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    # Grant-Table in eigener Session manipulieren (main thread)
    SessionLocal = app.state._SessionLocal
    with SessionLocal() as s:
        engine = s.get_bind()
        md = MetaData()
        grants = Table("export_grants_vehicle", md, autoload_with=engine)

        row = s.execute(select(grants).limit(1)).mappings().first()
        assert row

        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
        s.execute(update(grants).where(grants.c.id == row["id"]).values(expires_at=past))
        s.commit()

    f = client.get("/export/vehicle/veh_1/full", headers={"X-Export-Token": tok})
    assert f.status_code == 403
