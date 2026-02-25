from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.actor import require_actor
from app.guards import forbid_moderator
from app.models.addons import AccountAddonEntitlement, AddonConfig, VehicleAddonState
from app.models.vehicle import Vehicle

try:
    from app.deps import get_db  # type: ignore
except Exception:  # pragma: no cover
    from app.db.session import get_db  # type: ignore


# ✅ WICHTIG: Export muss "router" heißen (main.py importiert das so)
router = APIRouter(prefix="/addons", tags=["addons"], dependencies=[Depends(forbid_moderator)])


def _role_of(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("role") or actor.get("role_name") or actor.get("role_id") or "")
    return str(getattr(actor, "role", None) or getattr(actor, "role_name", None) or getattr(actor, "role_id", None) or "")


def _user_id_of(actor: Any) -> str:
    if isinstance(actor, dict):
        uid = actor.get("user_id") or actor.get("id") or actor.get("subject")
    else:
        uid = getattr(actor, "user_id", None) or getattr(actor, "id", None) or getattr(actor, "subject", None)
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return str(uid)


def _is_admin(role: str) -> bool:
    return role in {"admin", "superadmin"}


def _deny_code(code: str) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": code})


def _assert_vehicle_scope(db: Session, actor: Any, vehicle_id: str) -> tuple[str, str, Vehicle]:
    uid = _user_id_of(actor)
    role = _role_of(actor)

    v = db.query(Vehicle).filter(Vehicle.public_id == str(vehicle_id)).first()
    if v is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(role) and str(v.owner_user_id) != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    return uid, role, v


class AddonConfigIn(BaseModel):
    allow_new: bool = False
    requires_payment: bool = True
    admin_only: bool = False


class AddonEntitlementIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    enabled: bool = True


class AddonEnableIn(BaseModel):
    addon_key: str = Field(min_length=1, max_length=64)


class AddonOut(BaseModel):
    vehicle_id: str
    addon_key: str
    active: bool
    addon_first_enabled_at: str | None


def _to_out(state: VehicleAddonState) -> AddonOut:
    ts = None
    if state.addon_first_enabled_at is not None:
        ts = state.addon_first_enabled_at.astimezone(timezone.utc).isoformat()
    return AddonOut(
        vehicle_id=str(state.vehicle_id),
        addon_key=str(state.addon_key),
        active=bool(state.active),
        addon_first_enabled_at=ts,
    )


@router.post("/config/{addon_key}")
def upsert_addon_config(
    addon_key: str,
    payload: AddonConfigIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> dict:
    role = _role_of(actor)
    if not _is_admin(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    row = db.query(AddonConfig).filter(AddonConfig.addon_key == addon_key).first()
    if row is None:
        row = AddonConfig(addon_key=addon_key)
        db.add(row)

    row.allow_new = payload.allow_new
    row.requires_payment = payload.requires_payment
    row.admin_only = payload.admin_only

    db.commit()
    return {"ok": True}


@router.post("/entitlements/{addon_key}")
def upsert_addon_entitlement(
    addon_key: str,
    payload: AddonEntitlementIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> dict:
    role = _role_of(actor)
    if not _is_admin(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    row = (
        db.query(AccountAddonEntitlement)
        .filter(AccountAddonEntitlement.user_id == payload.user_id, AccountAddonEntitlement.addon_key == addon_key)
        .first()
    )
    if row is None:
        row = AccountAddonEntitlement(user_id=payload.user_id, addon_key=addon_key)
        db.add(row)

    row.enabled = payload.enabled
    db.commit()
    return {"ok": True}


@router.post("/vehicles/{vehicle_id}/enable", response_model=AddonOut)
def enable_addon(
    vehicle_id: str,
    payload: AddonEnableIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> AddonOut:
    uid, role, _v = _assert_vehicle_scope(db, actor, vehicle_id)

    state = (
        db.query(VehicleAddonState)
        .filter(VehicleAddonState.vehicle_id == str(vehicle_id), VehicleAddonState.addon_key == payload.addon_key)
        .first()
    )

    # ✅ Grandfathering: addon_first_enabled_at gesetzt => Re-Enable immer erlaubt
    if state is not None and state.addon_first_enabled_at is not None:
        state.active = True
        db.commit()
        db.refresh(state)
        return _to_out(state)

    config = db.query(AddonConfig).filter(AddonConfig.addon_key == payload.addon_key).first()
    if config is None:
        _deny_code("addon_not_available")

    if config.admin_only and not _is_admin(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    if not config.allow_new:
        _deny_code("addon_not_available")

    if config.requires_payment and not _is_admin(role):
        ent = (
            db.query(AccountAddonEntitlement)
            .filter(
                AccountAddonEntitlement.user_id == uid,
                AccountAddonEntitlement.addon_key == payload.addon_key,
                AccountAddonEntitlement.enabled.is_(True),
            )
            .first()
        )
        if ent is None:
            _deny_code("paywall_required")

    now = datetime.now(timezone.utc)
    if state is None:
        state = VehicleAddonState(
            vehicle_id=str(vehicle_id),
            addon_key=payload.addon_key,
            active=True,
            addon_first_enabled_at=now,
        )
        db.add(state)
    else:
        state.active = True
        if state.addon_first_enabled_at is None:
            state.addon_first_enabled_at = now

    db.commit()
    db.refresh(state)
    return _to_out(state)


@router.post("/vehicles/{vehicle_id}/disable", response_model=AddonOut)
def disable_addon(
    vehicle_id: str,
    payload: AddonEnableIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> AddonOut:
    _uid, _role, _v = _assert_vehicle_scope(db, actor, vehicle_id)

    state = (
        db.query(VehicleAddonState)
        .filter(VehicleAddonState.vehicle_id == str(vehicle_id), VehicleAddonState.addon_key == payload.addon_key)
        .first()
    )
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    state.active = False
    db.commit()
    db.refresh(state)
    return _to_out(state)


@router.get("/vehicles/{vehicle_id}/{addon_key}", response_model=AddonOut)
def get_addon_state(
    vehicle_id: str,
    addon_key: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> AddonOut:
    _uid, _role, _v = _assert_vehicle_scope(db, actor, vehicle_id)

    state = (
        db.query(VehicleAddonState)
        .filter(VehicleAddonState.vehicle_id == str(vehicle_id), VehicleAddonState.addon_key == addon_key)
        .first()
    )
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    return _to_out(state)
