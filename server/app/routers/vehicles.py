from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.actor import require_actor
from app.guards import forbid_moderator

try:
    from app.deps import get_db  # type: ignore
except Exception:  # pragma: no cover
    from app.db.session import get_db  # type: ignore

from app.models.vehicle import Vehicle
from app.models.vehicle_entry import VehicleEntry

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{11,17}$")  # excludes I,O,Q
ALLOWED_ROLES = {"user", "vip", "dealer", "admin", "superadmin"}


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


def _normalize_vin(vin: str) -> str:
    v = (vin or "").strip().upper().replace(" ", "")
    if not VIN_RE.match(v):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_vin_format")
    return v


def require_consent(db: Session, actor: Any) -> None:
    uid = _user_id_of(actor)

    try:
        from app.services.consent_store import has_required_consents  # type: ignore
        if has_required_consents(db, uid):
            return
    except Exception:
        pass

    try:
        import app.consent_store as cs  # type: ignore
        required_version = cs.env_consent_version()
        st = cs.get_consent_status(cs.env_db_path(), uid, required_version)
        ok = False
        if isinstance(st, dict):
            ok = bool(st.get("ok") or st.get("has_required") or st.get("accepted"))
        else:
            ok = bool(getattr(st, "ok", False) or getattr(st, "has_required", False) or getattr(st, "accepted", False))
        if ok:
            return
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="consent_required")


class VehicleCreateIn(BaseModel):
    vin: str = Field(..., min_length=11, max_length=17)
    nickname: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class VehicleOut(BaseModel):
    id: str
    vin_masked: str
    nickname: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class VehicleEntryCreateIn(BaseModel):
    date: date
    type: str = Field(..., min_length=1, max_length=64)
    performed_by: str = Field(..., min_length=1, max_length=64)
    km: int = Field(..., ge=0)
    note: Optional[str] = Field(default=None, max_length=4000)
    cost_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    trust_level: Optional[str] = Field(default=None, pattern="^(T1|T2|T3)$")


class VehicleEntryOut(BaseModel):
    id: str
    vehicle_id: str
    entry_group_id: str
    supersedes_entry_id: Optional[str] = None
    version: int
    revision_count: int
    is_latest: bool
    date: date
    type: str
    performed_by: str
    km: int
    note: Optional[str] = None
    cost_amount: Optional[float] = None
    trust_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime


def _require_consent_dep(
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> None:
    require_consent(db, actor)
router = APIRouter(prefix="/vehicles", tags=["vehicles"], dependencies=[Depends(forbid_moderator), Depends(_require_consent_dep)])


def _enforce_role(actor: Any) -> str:
    role = _role_of(actor)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return role


def _to_out(v: Vehicle) -> VehicleOut:
    nick = None
    if isinstance(v.meta, dict):
        nick = v.meta.get("nickname")
    return VehicleOut(id=v.public_id, vin_masked=v.vin_masked or "", nickname=nick, meta=v.meta)


def _load_vehicle_for_actor(db: Session, actor: Any, vehicle_id: str) -> Vehicle:
    role = _enforce_role(actor)
    uid = _user_id_of(actor)

    v = db.query(Vehicle).filter(Vehicle.public_id == str(vehicle_id)).first()
    if v is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if role in {"admin", "superadmin"}:
        return v

    if v.owner_user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    return v


def _revision_counts(db: Session, vehicle_id: str) -> dict[str, int]:
    rows = (
        db.query(VehicleEntry.entry_group_id, func.count(VehicleEntry.id))
        .filter(VehicleEntry.vehicle_id == vehicle_id)
        .group_by(VehicleEntry.entry_group_id)
        .all()
    )
    return {group_id: count for group_id, count in rows}


def _entry_to_out(entry: VehicleEntry, revision_count: int) -> VehicleEntryOut:
    cost_amount = float(entry.cost_amount) if entry.cost_amount is not None else None
    return VehicleEntryOut(
        id=entry.id,
        vehicle_id=entry.vehicle_id,
        entry_group_id=entry.entry_group_id,
        supersedes_entry_id=entry.supersedes_entry_id,
        version=entry.version,
        revision_count=revision_count,
        is_latest=entry.is_latest,
        date=entry.entry_date,
        type=entry.entry_type,
        performed_by=entry.performed_by,
        km=entry.km,
        note=entry.note,
        cost_amount=cost_amount,
        trust_level=entry.trust_level,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.post("", response_model=VehicleOut)
@router.post("/", response_model=VehicleOut)
def create_vehicle(payload: VehicleCreateIn, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> VehicleOut:
    try:
        role = _enforce_role(actor)
        uid = _user_id_of(actor)

        if role == "user":
            if db.query(Vehicle).filter(Vehicle.owner_user_id == uid).count() >= 1:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="vehicle_limit_reached")

        vin = _normalize_vin(payload.vin)

        meta = dict(payload.meta or {})
        if payload.nickname:
            meta["nickname"] = payload.nickname

        v = Vehicle(owner_user_id=uid, meta=meta or None)
        v.set_vin_from_raw(vin)

        db.add(v)
        db.commit()
        db.refresh(v)
        return _to_out(v)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.get("", response_model=list[VehicleOut])
@router.get("/", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> list[VehicleOut]:
    try:
        role = _enforce_role(actor)
        uid = _user_id_of(actor)

        q = db.query(Vehicle)
        if role not in {"admin", "superadmin"}:
            q = q.filter(Vehicle.owner_user_id == uid)

        return [_to_out(v) for v in q.all()]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> VehicleOut:
    try:
        v = _load_vehicle_for_actor(db, actor, vehicle_id)
        return _to_out(v)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.get("/{vehicle_id}/entries", response_model=list[VehicleEntryOut])
def list_vehicle_entries(vehicle_id: str, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> list[VehicleEntryOut]:
    try:
        vehicle = _load_vehicle_for_actor(db, actor, vehicle_id)
        revision_counts = _revision_counts(db, vehicle.public_id)
        entries = (
            db.query(VehicleEntry)
            .filter(VehicleEntry.vehicle_id == vehicle.public_id, VehicleEntry.is_latest.is_(True))
            .order_by(VehicleEntry.entry_date.desc(), VehicleEntry.created_at.desc())
            .all()
        )
        return [_entry_to_out(entry, revision_counts.get(entry.entry_group_id, 1)) for entry in entries]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.get("/{vehicle_id}/entries/{entry_id}/history", response_model=list[VehicleEntryOut])
def get_vehicle_entry_history(
    vehicle_id: str,
    entry_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> list[VehicleEntryOut]:
    try:
        vehicle = _load_vehicle_for_actor(db, actor, vehicle_id)
        anchor = (
            db.query(VehicleEntry)
            .filter(VehicleEntry.vehicle_id == vehicle.public_id, VehicleEntry.id == entry_id)
            .first()
        )
        if anchor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry_not_found")

        history = (
            db.query(VehicleEntry)
            .filter(VehicleEntry.vehicle_id == vehicle.public_id, VehicleEntry.entry_group_id == anchor.entry_group_id)
            .order_by(VehicleEntry.version.asc(), VehicleEntry.created_at.asc())
            .all()
        )
        revision_count = len(history)
        return [_entry_to_out(entry, revision_count) for entry in history]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.post("/{vehicle_id}/entries", response_model=VehicleEntryOut, status_code=status.HTTP_201_CREATED)
def create_vehicle_entry(
    vehicle_id: str,
    payload: VehicleEntryCreateIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleEntryOut:
    try:
        vehicle = _load_vehicle_for_actor(db, actor, vehicle_id)
        entry_id = str(uuid.uuid4())
        entry = VehicleEntry(
            id=entry_id,
            vehicle_id=vehicle.public_id,
            owner_user_id=vehicle.owner_user_id,
            entry_group_id=entry_id,
            version=1,
            is_latest=True,
            entry_date=payload.date,
            entry_type=payload.type.strip(),
            performed_by=payload.performed_by.strip(),
            km=payload.km,
            note=payload.note.strip() if isinstance(payload.note, str) and payload.note.strip() else None,
            cost_amount=payload.cost_amount,
            trust_level=payload.trust_level,
        )
        entry.entry_group_id = entry.id
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return _entry_to_out(entry, 1)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")


@router.post("/{vehicle_id}/entries/{entry_id}/revisions", response_model=VehicleEntryOut, status_code=status.HTTP_201_CREATED)
def create_vehicle_entry_revision(
    vehicle_id: str,
    entry_id: str,
    payload: VehicleEntryCreateIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleEntryOut:
    try:
        vehicle = _load_vehicle_for_actor(db, actor, vehicle_id)
        current = (
            db.query(VehicleEntry)
            .filter(
                VehicleEntry.vehicle_id == vehicle.public_id,
                VehicleEntry.id == entry_id,
                VehicleEntry.is_latest.is_(True),
            )
            .first()
        )
        if current is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry_not_found")

        current.is_latest = False
        revision = VehicleEntry(
            vehicle_id=vehicle.public_id,
            owner_user_id=vehicle.owner_user_id,
            entry_group_id=current.entry_group_id,
            supersedes_entry_id=current.id,
            version=current.version + 1,
            is_latest=True,
            entry_date=payload.date,
            entry_type=payload.type.strip(),
            performed_by=payload.performed_by.strip(),
            km=payload.km,
            note=payload.note.strip() if isinstance(payload.note, str) and payload.note.strip() else None,
            cost_amount=payload.cost_amount,
            trust_level=payload.trust_level,
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)
        return _entry_to_out(revision, revision.version)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")
