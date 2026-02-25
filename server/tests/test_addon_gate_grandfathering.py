from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import create_app
from app.models.vehicle import Vehicle


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
    from app.deps import get_db

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[require_actor] = lambda: actor_holder["actor"]

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


def test_grandfathering_allows_reenable_without_entitlement() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-1", public_id="veh-gf")

    _set_config(client, actor_holder, "restauration", allow_new=True, requires_payment=True, admin_only=False)

    _as(actor_holder, "admin-1", "admin")
    r1 = client.post("/addons/vehicles/veh-gf/enable", json={"addon_key": "restauration"})
    assert r1.status_code == 200, r1.text
    first_ts = r1.json().get("addon_first_enabled_at")
    assert first_ts

    _as(actor_holder, "u-1", "vip")
    r2 = client.post("/addons/vehicles/veh-gf/disable", json={"addon_key": "restauration"})
    assert r2.status_code == 200, r2.text

    r3 = client.post("/addons/vehicles/veh-gf/enable", json={"addon_key": "restauration"})
    assert r3.status_code == 200, r3.text
    assert r3.json().get("addon_first_enabled_at") == first_ts


def test_new_activation_allow_new_false_returns_addon_not_available() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-2", public_id="veh-closed")

    _set_config(client, actor_holder, "oldtimer", allow_new=False, requires_payment=False, admin_only=False)

    _as(actor_holder, "u-2", "vip")
    r = client.post("/addons/vehicles/veh-closed/enable", json={"addon_key": "oldtimer"})
    assert r.status_code == 403, r.text
    assert r.json().get("detail", {}).get("code") == "addon_not_available"


def test_new_activation_requires_payment_without_entitlement_returns_paywall_required() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-3", public_id="veh-pay")

    _set_config(client, actor_holder, "premium_docs", allow_new=True, requires_payment=True, admin_only=False)

    _as(actor_holder, "u-3", "vip")
    r = client.post("/addons/vehicles/veh-pay/enable", json={"addon_key": "premium_docs"})
    assert r.status_code == 403, r.text
    assert r.json().get("detail", {}).get("code") == "paywall_required"


def test_new_activation_with_entitlement_is_allowed_and_sets_first_enabled() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-4", public_id="veh-ent")

    _set_config(client, actor_holder, "premium_docs", allow_new=True, requires_payment=True, admin_only=False)

    _as(actor_holder, "admin-1", "admin")
    e = client.post("/addons/entitlements/premium_docs", json={"user_id": "u-4", "enabled": True})
    assert e.status_code == 200, e.text

    _as(actor_holder, "u-4", "vip")
    r = client.post("/addons/vehicles/veh-ent/enable", json={"addon_key": "premium_docs"})
    assert r.status_code == 200, r.text
    assert r.json().get("addon_first_enabled_at") is not None


def test_admin_only_blocks_vip_and_allows_admin() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-5", public_id="veh-admin-only")

    _set_config(client, actor_holder, "internal_tool", allow_new=True, requires_payment=False, admin_only=True)

    _as(actor_holder, "u-5", "vip")
    rv = client.post("/addons/vehicles/veh-admin-only/enable", json={"addon_key": "internal_tool"})
    assert rv.status_code == 403, rv.text

    _as(actor_holder, "admin-1", "admin")
    ra = client.post("/addons/vehicles/veh-admin-only/enable", json={"addon_key": "internal_tool"})
    assert ra.status_code == 200, ra.text


def test_moderator_block_and_unauth_on_addon_routes() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="m-1", public_id="veh-mod")

    _as(actor_holder, "m-1", "moderator")
    rm = client.post("/addons/vehicles/veh-mod/enable", json={"addon_key": "x"})
    assert rm.status_code == 403, rm.text

    app = create_app()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal2 = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    from app.deps import get_db

    def _get_db2():
        db = SessionLocal2()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db2
    unauth_client = TestClient(app)
    ru = unauth_client.post("/addons/vehicles/veh-mod/enable", json={"addon_key": "x"})
    assert ru.status_code == 401, ru.text


def test_unknown_addon_key_is_deny_by_default() -> None:
    client, SessionLocal, actor_holder = _setup()

    with SessionLocal() as db:
        _create_vehicle(db, owner_user_id="u-6", public_id="veh-unknown")

    _as(actor_holder, "u-6", "vip")
    r = client.post("/addons/vehicles/veh-unknown/enable", json={"addon_key": "unknown-addon"})
    assert r.status_code == 403, r.text
    assert r.json().get("detail", {}).get("code") == "addon_not_available"
