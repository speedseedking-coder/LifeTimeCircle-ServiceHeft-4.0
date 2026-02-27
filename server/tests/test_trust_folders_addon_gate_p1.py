from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import create_app
from app.models.addons import VehicleAddonState
from app.models.trust_folder import TrustFolder
from app.models.vehicle import Vehicle
from app.rbac import get_current_user


def _setup():
    app = create_app()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    actor_holder: dict[str, object] = {
        "actor": {"user_id": "init", "role": "admin"},
    }

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.auth.actor import require_actor
    from app.consent import guard as consent_guard
    from app.deps import get_db

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[require_actor] = lambda: actor_holder["actor"]
    app.dependency_overrides[get_current_user] = lambda: actor_holder["actor"]

    async def _consent_ok():
        return None

    app.dependency_overrides[consent_guard.require_consent] = _consent_ok

    client = TestClient(app)
    return client, SessionLocal, actor_holder


def _as(actor_holder: dict, user_id: str, role: str) -> None:
    actor_holder["actor"] = {"user_id": user_id, "role": role}


def _create_vehicle(db, owner_user_id: str, public_id: str) -> None:
    v = Vehicle(owner_user_id=owner_user_id)
    v.public_id = public_id
    db.add(v)
    db.commit()


def _set_config(client: TestClient, actor_holder: dict, addon_key: str, *, allow_new: bool, requires_payment: bool, admin_only: bool) -> None:
    _as(actor_holder, "admin-1", "admin")
    res = client.post(
        f"/addons/config/{addon_key}",
        json={
            "allow_new": allow_new,
            "requires_payment": requires_payment,
            "admin_only": admin_only,
        },
    )
    assert res.status_code == 200, res.text


def test_deny_by_default_paywall_required_without_entitlement() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-1", public_id="veh-pay")

    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=True, admin_only=False)

    _as(actor_holder, "u-1", "vip")
    res = client.post("/trust/folders", json={"vehicle_id": "veh-pay", "title": "A", "addon_key": "restauration"})
    assert res.status_code == 403, res.text
    assert res.json().get("detail", {}).get("code") == "paywall_required"


def test_deny_by_default_unknown_addon_returns_addon_not_available() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-2", public_id="veh-unknown")

    _as(actor_holder, "u-2", "vip")
    res = client.post("/trust/folders", json={"vehicle_id": "veh-unknown", "title": "A", "addon_key": "unknown-addon"})
    assert res.status_code == 403, res.text
    assert res.json().get("detail", {}).get("code") == "addon_not_available"


def test_grandfathering_with_first_enabled_allows_access() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-3", public_id="veh-gf")
        db.add(
            VehicleAddonState(
                vehicle_id="veh-gf",
                addon_key="restauration",
                active=False,
                addon_first_enabled_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    _as(actor_holder, "u-3", "vip")
    res = client.post("/trust/folders", json={"vehicle_id": "veh-gf", "title": "GF", "addon_key": "restauration"})
    assert res.status_code == 201, res.text


def test_grandfathering_backfill_sets_first_enabled_when_data_exists() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-4", public_id="veh-backfill")
        db.add(
            VehicleAddonState(
                vehicle_id="veh-backfill",
                addon_key="restauration",
                active=False,
                addon_first_enabled_at=None,
            )
        )
        db.add(TrustFolder(vehicle_id="veh-backfill", owner_user_id="u-4", addon_key="restauration", title="Legacy"))
        db.commit()

    _as(actor_holder, "u-4", "vip")
    res = client.get("/trust/folders", params={"vehicle_id": "veh-backfill", "addon_key": "restauration"})
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1

    with SessionLocal() as db:
        state = (
            db.query(VehicleAddonState)
            .filter(VehicleAddonState.vehicle_id == "veh-backfill", VehicleAddonState.addon_key == "restauration")
            .first()
        )
        assert state is not None
        assert state.addon_first_enabled_at is not None


def test_grandfathering_backfill_state_missing_is_allowed_if_legacy_data_exists() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-8", public_id="veh-legacy-nostate")
        # Legacy data exists, but NO VehicleAddonState row
        db.add(TrustFolder(vehicle_id="veh-legacy-nostate", owner_user_id="u-8", addon_key="restauration", title="Legacy"))
        db.commit()

    # requires_payment=True would normally block, but legacy data must be grandfathered
    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=True, admin_only=False)

    _as(actor_holder, "u-8", "vip")
    res = client.get("/trust/folders", params={"vehicle_id": "veh-legacy-nostate", "addon_key": "restauration"})
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1

    with SessionLocal() as db:
        state = (
            db.query(VehicleAddonState)
            .filter(VehicleAddonState.vehicle_id == "veh-legacy-nostate", VehicleAddonState.addon_key == "restauration")
            .first()
        )
        assert state is not None
        assert state.addon_first_enabled_at is not None


def test_moderator_gets_403_on_all_trust_folder_routes() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="mod-1", public_id="veh-mod")

    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=False, admin_only=False)
    _as(actor_holder, "mod-1", "moderator")

    r_post = client.post("/trust/folders", json={"vehicle_id": "veh-mod", "title": "M", "addon_key": "restauration"})
    assert r_post.status_code == 403, r_post.text

    r_list = client.get("/trust/folders", params={"vehicle_id": "veh-mod", "addon_key": "restauration"})
    assert r_list.status_code == 403, r_list.text


def test_owner_scope_blocks_other_user_and_admin_override_allowed() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="owner-1", public_id="veh-owner")

    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=False, admin_only=False)

    _as(actor_holder, "owner-1", "vip")
    created = client.post(
        "/trust/folders",
        json={"vehicle_id": "veh-owner", "title": "Owner Folder", "addon_key": "restauration"},
    )
    assert created.status_code == 201, created.text
    folder_id = created.json()["id"]

    _as(actor_holder, "user-2", "vip")
    forbidden = client.get(f"/trust/folders/{folder_id}")
    assert forbidden.status_code == 403, forbidden.text

    _as(actor_holder, "admin-9", "admin")
    allowed = client.get(f"/trust/folders/{folder_id}")
    assert allowed.status_code == 200, allowed.text


def test_consent_gate_blocks_productive_route() -> None:
    client, SessionLocal, actor_holder = _setup()

    from app.consent import guard as consent_guard

    async def _consent_block():
        raise HTTPException(status_code=403, detail="consent_required")

    client.app.dependency_overrides[consent_guard.require_consent] = _consent_block

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-7", public_id="veh-consent")

    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=False, admin_only=False)

    _as(actor_holder, "u-7", "vip")
    res = client.post("/trust/folders", json={"vehicle_id": "veh-consent", "title": "X", "addon_key": "restauration"})
    assert res.status_code == 403, res.text
    assert res.json().get("detail") == "consent_required"