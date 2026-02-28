import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("LTC_SECRET_KEY", "dev_test_secret_key_32_chars_minimum__OK")


class ActorStub(dict):
    def __getattr__(self, item):
        return self.get(item)


def _wire_app(mem_db, actor: ActorStub, monkeypatch, bypass_consent: bool = True):
    from app.routers import vehicles as vehicles_mod  # type: ignore

    app = FastAPI()
    app.include_router(vehicles_mod.router)

    def _get_db():
        yield mem_db

    app.dependency_overrides[vehicles_mod.get_db] = _get_db  # type: ignore
    app.dependency_overrides[vehicles_mod.require_actor] = lambda: actor  # type: ignore

    if bypass_consent:
        monkeypatch.setattr(vehicles_mod, "require_consent", lambda db, actor: None, raising=True)

    return app


def _mem_db():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    from app.db.base import Base  # type: ignore
    from app.models.vehicle import Vehicle  # noqa: F401
    from app.models.vehicle_entry import VehicleEntry  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_vehicle_entries_create_list_history_and_revision(monkeypatch):
    db = _mem_db()
    try:
        actor = ActorStub(user_id="u1", role="user")
        client = TestClient(_wire_app(db, actor, monkeypatch))

        vehicle_res = client.post("/vehicles", json={"vin": "WVWZZZ1JZXW000001"})
        assert vehicle_res.status_code == 200, vehicle_res.text
        vehicle_id = vehicle_res.json()["id"]

        create_res = client.post(
            f"/vehicles/{vehicle_id}/entries",
            json={
                "date": "2026-02-28",
                "type": "Service",
                "performed_by": "Eigenleistung",
                "km": 123456,
                "note": "Erster Eintrag",
                "cost_amount": 120.5,
                "trust_level": "T2",
            },
        )
        assert create_res.status_code == 201, create_res.text
        entry = create_res.json()
        assert entry["version"] == 1
        assert entry["revision_count"] == 1
        assert entry["note"] == "Erster Eintrag"

        list_res = client.get(f"/vehicles/{vehicle_id}/entries")
        assert list_res.status_code == 200, list_res.text
        listed = list_res.json()
        assert len(listed) == 1
        assert listed[0]["id"] == entry["id"]

        revision_res = client.post(
            f"/vehicles/{vehicle_id}/entries/{entry['id']}/revisions",
            json={
                "date": "2026-03-01",
                "type": "Service",
                "performed_by": "Werkstatt",
                "km": 123900,
                "note": "Korrigierte Version",
                "cost_amount": 150,
                "trust_level": "T3",
            },
        )
        assert revision_res.status_code == 201, revision_res.text
        revision = revision_res.json()
        assert revision["version"] == 2
        assert revision["supersedes_entry_id"] == entry["id"]

        list_after_revision = client.get(f"/vehicles/{vehicle_id}/entries")
        assert list_after_revision.status_code == 200, list_after_revision.text
        latest = list_after_revision.json()
        assert len(latest) == 1
        assert latest[0]["id"] == revision["id"]
        assert latest[0]["revision_count"] == 2
        assert latest[0]["performed_by"] == "Werkstatt"

        history_res = client.get(f"/vehicles/{vehicle_id}/entries/{revision['id']}/history")
        assert history_res.status_code == 200, history_res.text
        history = history_res.json()
        assert [item["version"] for item in history] == [1, 2]
        assert history[0]["is_latest"] is False
        assert history[1]["is_latest"] is True
    finally:
        db.close()


def test_vehicle_entries_owner_scope_enforced(monkeypatch):
    db = _mem_db()
    try:
        owner = ActorStub(user_id="owner", role="user")
        owner_client = TestClient(_wire_app(db, owner, monkeypatch))

        vehicle_res = owner_client.post("/vehicles", json={"vin": "WVWZZZ1JZXW000001"})
        vehicle_id = vehicle_res.json()["id"]
        entry_res = owner_client.post(
            f"/vehicles/{vehicle_id}/entries",
            json={
                "date": "2026-02-28",
                "type": "Service",
                "performed_by": "Eigenleistung",
                "km": 10,
            },
        )
        entry_id = entry_res.json()["id"]

        stranger = ActorStub(user_id="stranger", role="user")
        stranger_client = TestClient(_wire_app(db, stranger, monkeypatch))

        denied_list = stranger_client.get(f"/vehicles/{vehicle_id}/entries")
        assert denied_list.status_code == 403, denied_list.text

        denied_history = stranger_client.get(f"/vehicles/{vehicle_id}/entries/{entry_id}/history")
        assert denied_history.status_code == 403, denied_history.text
    finally:
        db.close()
