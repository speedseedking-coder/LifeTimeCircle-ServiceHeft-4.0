from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.routers import documents as documents_router
from app.routers import export_vehicle
from app.services.documents_store import DocumentsStore


def test_documents_rejects_legacy_x_ltc_headers_without_dev_gate(monkeypatch) -> None:
    monkeypatch.delenv("LTC_ALLOW_DEV_HEADERS", raising=False)

    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=Path(td) / "storage",
            db_path=Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )

        app = FastAPI()
        app.include_router(documents_router.router)
        app.dependency_overrides[documents_router.get_documents_store] = lambda: store

        with TestClient(app) as client:
            response = client.get(
                "/documents/admin/quarantine",
                headers={"X-LTC-ROLE": "admin", "X-LTC-UID": "dev-admin"},
            )
            assert response.status_code == 401, response.text


def test_export_vehicle_rejects_legacy_x_ltc_headers_without_dev_gate(monkeypatch) -> None:
    monkeypatch.delenv("LTC_ALLOW_DEV_HEADERS", raising=False)
    monkeypatch.setenv("LTC_SECRET_KEY", "dev-only-change-me-please-change-me-32chars-XXXX")

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

    with engine.begin() as conn:
        conn.execute(insert(vehicles).values(id="veh_1", owner_id="user_1"))

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    app = FastAPI()
    app.include_router(export_vehicle.router)

    def override_get_db():
        with SessionLocal() as session:
            yield session

    app.dependency_overrides[export_vehicle.get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get(
            "/export/vehicle/veh_1",
            headers={"X-LTC-ROLE": "user", "X-LTC-UID": "user_1"},
        )
        assert response.status_code == 401, response.text
