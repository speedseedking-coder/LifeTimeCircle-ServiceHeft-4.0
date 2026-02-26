from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.actor import require_actor
from app.consent.guard import require_consent
from app.guards import forbid_moderator
from app.models.addons import AccountAddonEntitlement, AddonConfig, VehicleAddonState
from app.models.trust_folder import TrustFolder
from app.models.vehicle import Vehicle

try:
    from app.deps import get_db  # type: ignore
except Exception:  # pragma: no cover
    from app.db.session import get_db  # type: ignore


router = APIRouter(
    prefix="/trust/folders",
    tags=["trust", "folders"],
    dependencies=[Depends(forbid_moderator), Depends(require_consent)],
)

_ALLOWED_ROLES = {"vip", "dealer", "admin", "superadmin"}


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


def _assert_allowed_role(actor: Any) -> tuple[str, str]:
    role = _role_of(actor)
    if role not in _ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return _user_id_of(actor), role


def _assert_vehicle_scope(db: Session, actor: Any, vehicle_id: str) -> tuple[str, str, Vehicle]:
    uid, role = _assert_allowed_role(actor)

    vehicle = db.query(Vehicle).filter(Vehicle.public_id == str(vehicle_id)).first()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(role) and str(vehicle.owner_user_id) != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    return uid, role, vehicle


def _ensure_addon_enabled_or_block(
    db: Session,
    *,
    uid: str,
    role: str,
    vehicle_id: str,
    addon_key: str,
) -> VehicleAddonState:
    state = (
        db.query(VehicleAddonState)
        .filter(VehicleAddonState.vehicle_id == str(vehicle_id), VehicleAddonState.addon_key == addon_key)
        .first()
    )

    # Grandfathering: once addon_first_enabled_at is set => always allow
    if state is not None and state.addon_first_enabled_at is not None:
        return state

    config = db.query(AddonConfig).filter(AddonConfig.addon_key == addon_key).first()
    if config is None:
        _deny_code("addon_not_available")

    if config.admin_only and not _is_admin(role):
        _deny_code("admin_only")

    if not config.allow_new:
        _deny_code("addon_not_available")

    if config.requires_payment and not _is_admin(role):
        ent = (
            db.query(AccountAddonEntitlement)
            .filter(
                AccountAddonEntitlement.user_id == uid,
                AccountAddonEntitlement.addon_key == addon_key,
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
            addon_key=addon_key,
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
    return state


def _ensure_grandfathered_if_existing_data(
    db: Session,
    *,
    vehicle_id: str,
    addon_key: str,
) -> None:
    """
    Backfill-Schutz:
    - Wenn legacy TrustFolder-Daten existieren, darf ein später aktiviertes Gate nicht blocken.
    - Daher: addon_first_enabled_at serverseitig setzen, auch wenn noch kein VehicleAddonState Row existiert.
    """
    state = (
        db.query(VehicleAddonState)
        .filter(VehicleAddonState.vehicle_id == str(vehicle_id), VehicleAddonState.addon_key == addon_key)
        .first()
    )

    if state is not None and state.addon_first_enabled_at is not None:
        return

    has_existing_folders = (
        db.query(TrustFolder.id)
        .filter(TrustFolder.vehicle_id == str(vehicle_id), TrustFolder.addon_key == addon_key)
        .first()
    )
    if has_existing_folders is None:
        return

    now = datetime.now(timezone.utc)

    if state is None:
        state = VehicleAddonState(
            vehicle_id=str(vehicle_id),
            addon_key=addon_key,
            active=True,
            addon_first_enabled_at=now,
        )
        db.add(state)
        db.commit()
        return

    state.addon_first_enabled_at = now
    state.active = True
    db.commit()


class TrustFolderCreateIn(BaseModel):
    vehicle_id: str = Field(min_length=1, max_length=36)
    title: str = Field(min_length=1, max_length=255)
    addon_key: str = Field(default="restauration", min_length=1, max_length=64)


class TrustFolderPatchIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class TrustFolderOut(BaseModel):
    id: int
    vehicle_id: str
    owner_user_id: str
    addon_key: str
    title: str


@router.get("", response_model=list[TrustFolderOut])
@router.get("/", response_model=list[TrustFolderOut])
def list_trust_folders(
    vehicle_id: str = Query(min_length=1),
    addon_key: str = Query(default="restauration", min_length=1, max_length=64),
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> list[TrustFolderOut]:
    uid, role, _vehicle = _assert_vehicle_scope(db, actor, vehicle_id)
    _ensure_grandfathered_if_existing_data(db, vehicle_id=vehicle_id, addon_key=addon_key)
    _ensure_addon_enabled_or_block(db, uid=uid, role=role, vehicle_id=vehicle_id, addon_key=addon_key)

    q = db.query(TrustFolder).filter(TrustFolder.vehicle_id == str(vehicle_id), TrustFolder.addon_key == addon_key)
    if not _is_admin(role):
        q = q.filter(TrustFolder.owner_user_id == uid)

    rows = q.order_by(TrustFolder.id.asc()).all()
    return [TrustFolderOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=TrustFolderOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TrustFolderOut, status_code=status.HTTP_201_CREATED)
def create_trust_folder(payload: TrustFolderCreateIn, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> TrustFolderOut:
    uid, role, _vehicle = _assert_vehicle_scope(db, actor, payload.vehicle_id)
    _ensure_grandfathered_if_existing_data(db, vehicle_id=payload.vehicle_id, addon_key=payload.addon_key)
    _ensure_addon_enabled_or_block(db, uid=uid, role=role, vehicle_id=payload.vehicle_id, addon_key=payload.addon_key)

    row = TrustFolder(
        vehicle_id=str(payload.vehicle_id),
        owner_user_id=uid,
        addon_key=payload.addon_key,
        title=payload.title.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TrustFolderOut.model_validate(row, from_attributes=True)


@router.get("/{folder_id}", response_model=TrustFolderOut)
def get_trust_folder(folder_id: int, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> TrustFolderOut:
    uid, role = _assert_allowed_role(actor)

    row = db.query(TrustFolder).filter(TrustFolder.id == folder_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(role) and row.owner_user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    _ensure_grandfathered_if_existing_data(db, vehicle_id=row.vehicle_id, addon_key=row.addon_key)
    _ensure_addon_enabled_or_block(db, uid=uid, role=role, vehicle_id=row.vehicle_id, addon_key=row.addon_key)
    return TrustFolderOut.model_validate(row, from_attributes=True)


@router.patch("/{folder_id}", response_model=TrustFolderOut)
def patch_trust_folder(
    folder_id: int,
    payload: TrustFolderPatchIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> TrustFolderOut:
    uid, role = _assert_allowed_role(actor)

    row = db.query(TrustFolder).filter(TrustFolder.id == folder_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(role) and row.owner_user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    _ensure_grandfathered_if_existing_data(db, vehicle_id=row.vehicle_id, addon_key=row.addon_key)
    _ensure_addon_enabled_or_block(db, uid=uid, role=role, vehicle_id=row.vehicle_id, addon_key=row.addon_key)

    row.title = payload.title.strip()
    db.commit()
    db.refresh(row)
    return TrustFolderOut.model_validate(row, from_attributes=True)


@router.delete("/{folder_id}")
def delete_trust_folder(folder_id: int, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> dict[str, bool]:
    uid, role = _assert_allowed_role(actor)

    row = db.query(TrustFolder).filter(TrustFolder.id == folder_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(role) and row.owner_user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    _ensure_grandfathered_if_existing_data(db, vehicle_id=row.vehicle_id, addon_key=row.addon_key)
    _ensure_addon_enabled_or_block(db, uid=uid, role=role, vehicle_id=row.vehicle_id, addon_key=row.addon_key)

    db.delete(row)
    db.commit()
    return {"ok": True}