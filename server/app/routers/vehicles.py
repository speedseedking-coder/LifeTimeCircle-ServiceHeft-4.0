from __future__ import annotations

import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.actor import require_actor
from app.guards import forbid_moderator

try:
    from app.deps import get_db  # type: ignore
except Exception:  # pragma: no cover
    from app.db.session import get_db  # type: ignore

from app.models.vehicle import Vehicle

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

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "consent_required"})


class VehicleCreateIn(BaseModel):
    vin: str = Field(..., min_length=11, max_length=17)
    nickname: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class VehicleOut(BaseModel):
    id: str
    vin_masked: str
    nickname: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


router = APIRouter(prefix="/vehicles", tags=["vehicles"], dependencies=[Depends(forbid_moderator)])


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


@router.post("", response_model=VehicleOut)
@router.post("/", response_model=VehicleOut)
def create_vehicle(payload: VehicleCreateIn, db: Session = Depends(get_db), actor: Any = Depends(require_actor)) -> VehicleOut:
    try:
        role = _enforce_role(actor)
        require_consent(db, actor)
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
        require_consent(db, actor)
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
        role = _enforce_role(actor)
        require_consent(db, actor)
        uid = _user_id_of(actor)

        v = db.query(Vehicle).filter(Vehicle.public_id == str(vehicle_id)).first()
        if v is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

        if role in {"admin", "superadmin"}:
            return _to_out(v)

        if v.owner_user_id != uid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

        return _to_out(v)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal_error")
