import os
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
    from app.models.vehicle_entry import VehicleEntry  # noqa: F401

    Base.metadata.create_all(bind=mem_engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _wire_vehicles_app(mem_db, actor: ActorStub, monkeypatch):
    from app.routers import vehicles as vehicles_mod  # type: ignore

    app = FastAPI()
    app.include_router(vehicles_mod.router)

    def _get_db():
        yield mem_db

    app.dependency_overrides[vehicles_mod.get_db] = _get_db  # type: ignore
    app.dependency_overrides[vehicles_mod.require_actor] = lambda: actor  # type: ignore
    monkeypatch.setattr(vehicles_mod, "require_consent", lambda db, actor: None, raising=True)
    return app


def _wire_public_app(mem_db):
    from app.public import routes as public_mod  # type: ignore

    app = FastAPI()
    app.include_router(public_mod.router)

    def _get_db():
        yield mem_db

    app.dependency_overrides[public_mod.get_db] = _get_db  # type: ignore
    return app


def test_vehicle_trust_summary_derives_from_entries_and_accident_status(mem_db, monkeypatch):
    from app.models.vehicle import Vehicle  # type: ignore
    from app.models.vehicle_entry import VehicleEntry  # type: ignore

    vehicle = Vehicle(owner_user_id="u1", meta={"nickname": "Demo", "accident_status": "unknown"})
    vehicle.set_vin_from_raw("WVWZZZ1JZXW000001")
    mem_db.add(vehicle)
    mem_db.commit()
    mem_db.refresh(vehicle)

    mem_db.add(
        VehicleEntry(
            vehicle_id=vehicle.public_id,
            owner_user_id="u1",
            entry_group_id="grp-1",
            version=1,
            is_latest=True,
            entry_date=date(2026, 2, 20),
            entry_type="Inspektion",
            performed_by="Werkstatt",
            km=123456,
            trust_level="T2",
        )
    )
    mem_db.commit()

    app = _wire_vehicles_app(mem_db, ActorStub(user_id="u1", role="user"), monkeypatch)
    client = TestClient(app)

    r = client.get(f"/vehicles/{vehicle.public_id}/trust-summary")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["trust_light"] == "orange"
    assert data["verification_level"] == "mittel"
    assert data["history_status"] == "vorhanden"
    assert data["evidence_status"] == "vorhanden"
    assert data["accident_status"] == "unbekannt"
    assert data["accident_status_label"] == "Unbekannt"
    assert data["top_trust_level"] == "T2"
    assert "accident_status_unknown_cap_orange" in data["reason_codes"]
    assert "t3_requires_document_missing" in data["reason_codes"]


def test_public_qr_uses_real_vehicle_trust_summary(mem_db):
    from app.models.vehicle import Vehicle  # type: ignore
    from app.models.vehicle_entry import VehicleEntry  # type: ignore

    vehicle = Vehicle(
        owner_user_id="u1",
        meta={"nickname": "Public Demo", "accident_status": "accident_free"},
    )
    vehicle.set_vin_from_raw("WVWZZZ1JZXW000001")
    mem_db.add(vehicle)
    mem_db.commit()
    mem_db.refresh(vehicle)

    mem_db.add(
        VehicleEntry(
            vehicle_id=vehicle.public_id,
            owner_user_id="u1",
            entry_group_id="grp-2",
            version=1,
            is_latest=True,
            entry_date=date(2026, 2, 21),
            entry_type="Service",
            performed_by="Werkstatt",
            km=120000,
            trust_level="T3",
        )
    )
    mem_db.commit()

    app = _wire_public_app(mem_db)
    client = TestClient(app)

    r = client.get(f"/public/qr/{vehicle.public_id}")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["trust_light"] == "gruen"
    assert data["verification_level"] == "hoch"
    assert data["history_status"] == "vorhanden"
    assert data["evidence_status"] == "vorhanden"
    assert data["accident_status"] == "unfallfrei"
    assert data["accident_status_label"] == "Unfallfrei"
