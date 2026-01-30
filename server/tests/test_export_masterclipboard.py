import datetime as dt
import os

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
    select,
    update,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.routers import export_masterclipboard
from app.services.export_crypto import decrypt_json


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    md = MetaData()
    mc = Table(
        "masterclipboard",
        md,
        Column("id", String, primary_key=True),
        Column("vehicle_public_id", String, nullable=True),
        Column("transcript", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=True),
    )
    md.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            insert(mc).values(
                id="mc_1",
                vehicle_public_id="veh_pub_123",
                transcript="Hallo, hier ist viel Freitext drin.",
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
    app.include_router(export_masterclipboard.router)

    def override_get_db():
        with SessionLocal() as s:
            yield s

    actor_box = {"actor": {"role": "dealer", "user_id": "d_1"}}

    def override_get_actor():
        return actor_box["actor"]

    app.dependency_overrides[export_masterclipboard.get_db] = override_get_db
    app.dependency_overrides[export_masterclipboard.get_actor] = override_get_actor

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


def test_redacted_export_dealer_allowed(app, client):
    set_actor(app, role="dealer", user_id="d_1")
    r = client.get("/export/masterclipboard/mc_1")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["_redacted"] is True
    assert "transcript" not in data
    assert "vehicle_public_id" not in data
    assert "vehicle_public_id_hmac" in data


def test_redacted_export_user_denied(app, client):
    set_actor(app, role="user", user_id="u_1")
    r = client.get("/export/masterclipboard/mc_1")
    assert r.status_code == 403


def test_moderator_blocked(app, client):
    set_actor(app, role="moderator", user_id="m_1")
    r = client.get("/export/masterclipboard/mc_1")
    assert r.status_code == 403
    r2 = client.post("/export/masterclipboard/mc_1/grant")
    assert r2.status_code == 403


def test_grant_and_full_one_time_token(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")

    g = client.post("/export/masterclipboard/mc_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    f1 = client.get("/export/masterclipboard/mc_1/full", headers={"X-Export-Token": tok})
    assert f1.status_code == 200
    ciphertext = f1.json()["ciphertext"]

    payload = decrypt_json(ciphertext)
    assert payload["target"] == "masterclipboard"
    assert payload["id"] == "mc_1"
    assert payload["masterclipboard"]["transcript"] == "Hallo, hier ist viel Freitext drin."

    # one-time => zweites Mal muss scheitern
    f2 = client.get("/export/masterclipboard/mc_1/full", headers={"X-Export-Token": tok})
    assert f2.status_code == 403


def test_full_requires_token(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")
    r = client.get("/export/masterclipboard/mc_1/full")
    assert r.status_code == 400


def test_ttl_enforced_without_sleep(app, client):
    set_actor(app, role="superadmin", user_id="sa_1")
    os.environ["LTC_EXPORT_TTL_SECONDS"] = "600"

    g = client.post("/export/masterclipboard/mc_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    SessionLocal = app.state._SessionLocal
    with SessionLocal() as s:
        engine = s.get_bind()
        md = MetaData()
        grants = Table("export_grants_masterclipboard", md, autoload_with=engine)

        row = (
            s.execute(
                select(grants)
                .where(grants.c.resource_type == "masterclipboard")
                .where(grants.c.resource_id == "mc_1")
                .limit(1)
            )
            .mappings()
            .first()
        )
        assert row

        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
        s.execute(update(grants).where(grants.c.id == row["id"]).values(expires_at=past))
        s.commit()

    f = client.get("/export/masterclipboard/mc_1/full", headers={"X-Export-Token": tok})
    assert f.status_code == 403

