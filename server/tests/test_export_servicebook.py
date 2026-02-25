import datetime as dt
import os
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    select,
    update,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    # ENV: Secret + Defaults
    monkeypatch.setenv("LTC_SECRET_KEY", "dev-only-change-me-please-change-me-32chars-XXXX")
    monkeypatch.setenv("LTC_EXPORT_TTL_SECONDS", "600")
    monkeypatch.setenv("LTC_EXPORT_MAX_USES", "1")

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    md = MetaData()
    sb = Table(
        "servicebook_entries",
        md,
        Column("id", String, primary_key=True),
        Column("servicebook_id", String, nullable=False),
        Column("owner_id", String, nullable=True),
        Column("entry_type", String, nullable=True),
        Column("notes", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=True),
    )
    md.create_all(engine)

    now = dt.datetime.now(dt.timezone.utc)
    with SessionLocal() as s:
        s.execute(
            sb.insert(),
            [
                {
                    "id": "e_1",
                    "servicebook_id": "sb_1",
                    "owner_id": "user_1",
                    "entry_type": "service",
                    "notes": "SENSITIVE FREE TEXT",
                    "created_at": now,
                },
                {
                    "id": "e_2",
                    "servicebook_id": "sb_1",
                    "owner_id": "user_1",
                    "entry_type": "repair",
                    "notes": "MORE TEXT",
                    "created_at": now,
                },
                {
                    "id": "e_3",
                    "servicebook_id": "sb_2",
                    "owner_id": "user_2",
                    "entry_type": "service",
                    "notes": "OTHER USER TEXT",
                    "created_at": now,
                },
            ],
        )
        s.commit()

    from app.main import create_app  # noqa
    from app.routers import export_servicebook  # noqa

    app = create_app()
    app.state._SessionLocal = SessionLocal

    # dependency overrides (DB)
    def _get_db():
        with SessionLocal() as s:
            yield s

    app.dependency_overrides[export_servicebook.get_db] = _get_db  # type: ignore

    return app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def set_actor(app: FastAPI, *, role: str, user_id: str):
    from app.routers import export_servicebook  # noqa

    def _get_actor():
        return SimpleNamespace(role=role, user_id=user_id)

    app.dependency_overrides[export_servicebook.get_actor] = _get_actor  # type: ignore


def test_redacted_servicebook_owner_allowed(app: FastAPI, client: TestClient):
    set_actor(app, role="user", user_id="user_1")
    r = client.get("/export/servicebook/sb_1")
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == "servicebook"
    assert body["id"] == "sb_1"
    assert isinstance(body["entries"], list)
    assert len(body["entries"]) >= 2
    # kein Freitext
    assert "notes" not in body["entries"][0]


def test_redacted_servicebook_admin_allowed_notes_redacted(app: FastAPI, client: TestClient):
    set_actor(app, role="admin", user_id="a_1")
    r = client.get("/export/servicebook/sb_1")
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == "servicebook"
    assert isinstance(body["entries"], list)
    assert len(body["entries"]) >= 1
    assert "notes" not in body["entries"][0]


def test_redacted_servicebook_scope_denied(app: FastAPI, client: TestClient):
    set_actor(app, role="user", user_id="user_2")
    r = client.get("/export/servicebook/sb_1")
    assert r.status_code == 403


def test_moderator_never_allowed(app: FastAPI, client: TestClient):
    set_actor(app, role="moderator", user_id="mod_1")
    r = client.get("/export/servicebook/sb_1")
    assert r.status_code == 403


def test_missing_is_404(app: FastAPI, client: TestClient):
    set_actor(app, role="admin", user_id="a_1")
    r = client.get("/export/servicebook/does_not_exist")
    assert r.status_code == 404


def test_grant_and_full_one_time_token(app: FastAPI, client: TestClient):
    set_actor(app, role="superadmin", user_id="sa_1")

    g = client.post("/export/servicebook/sb_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    f1 = client.get("/export/servicebook/sb_1/full", headers={"X-Export-Token": tok})
    assert f1.status_code == 200
    assert "ciphertext" in f1.json()

    # one-time => second use forbidden
    f2 = client.get("/export/servicebook/sb_1/full", headers={"X-Export-Token": tok})
    assert f2.status_code in (401, 403)


def test_full_missing_token_is_400(app: FastAPI, client: TestClient):
    set_actor(app, role="superadmin", user_id="sa_1")
    r = client.get("/export/servicebook/sb_1/full")
    assert r.status_code == 400


def test_ttl_enforced_without_sleep(app: FastAPI, client: TestClient):
    set_actor(app, role="superadmin", user_id="sa_1")

    os.environ["LTC_EXPORT_TTL_SECONDS"] = "600"
    g = client.post("/export/servicebook/sb_1/grant")
    assert g.status_code == 200
    tok = g.json()["export_token"]

    # Grant-Table manipulieren (main thread)
    SessionLocal = app.state._SessionLocal
    with SessionLocal() as s:
        engine = s.get_bind()
        md = MetaData()
        grants = Table("export_grants_servicebook", md, autoload_with=engine)

        row = s.execute(select(grants).limit(1)).mappings().first()
        assert row

        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
        s.execute(update(grants).where(grants.c.id == row["id"]).values(expires_at=past))
        s.commit()

    f = client.get("/export/servicebook/sb_1/full", headers={"X-Export-Token": tok})
    assert f.status_code in (401, 403)
