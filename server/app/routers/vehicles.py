from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Tuple, Type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.actor import require_actor
from app.guards import forbid_moderator
from app.deps import get_db


VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{11,17}$")  # excludes I,O,Q
ALLOWED_ROLES = {"user", "vip", "dealer", "admin", "superadmin"}


def _role_of(actor: Any) -> str:
    return (
        getattr(actor, "role", None)
        or getattr(actor, "role_name", None)
        or getattr(actor, "role_id", None)
        or ""
    )


def _actor_id(actor: Any) -> Any:
    return getattr(actor, "user_id", None) or getattr(actor, "id", None) or getattr(actor, "subject", None)


def _normalize_vin(vin: str) -> str:
    v = (vin or "").strip().upper().replace(" ", "")
    if not VIN_RE.match(v):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_vin_format",
        )
    return v


def _mask_vin(vin: str) -> str:
    if not vin:
        return ""
    if len(vin) <= 7:
        return vin[0:1] + "***" + vin[-1:]
    return f"{vin[:3]}***{vin[-4:]}"


def _get_vehicle_model() -> Type[Any]:
    candidates = [
        ("app.models.vehicle", "Vehicle"),
        ("app.models.vehicles", "Vehicle"),
        ("app.models.vehicle_model", "Vehicle"),
        ("app.models.vehicle_models", "Vehicle"),
    ]
    for mod, name in candidates:
        try:
            m = __import__(mod, fromlist=[name])
            return getattr(m, name)
        except Exception:
            continue
    raise RuntimeError("Vehicle model not found (expected app.models.*.Vehicle)")


def _get_servicebook_model() -> Optional[Type[Any]]:
    candidates = [
        ("app.models.servicebook", "Servicebook"),
        ("app.models.servicebook", "ServiceBook"),
        ("app.models.service_book", "Servicebook"),
        ("app.models.service_book", "ServiceBook"),
        ("app.models.servicebooks", "Servicebook"),
        ("app.models.servicebooks", "ServiceBook"),
    ]
    for mod, name in candidates:
        try:
            m = __import__(mod, fromlist=[name])
            return getattr(m, name)
        except Exception:
            continue
    return None


def _find_owner_col(Vehicle: Type[Any]) -> Tuple[Optional[str], Any]:
    for name in ("owner_user_id", "owner_id", "user_id", "created_by_user_id"):
        if hasattr(Vehicle, name):
            return name, getattr(Vehicle, name)
    return None, None


def _coerce_pk(pk: str) -> Any:
    if pk.isdigit():
        try:
            return int(pk)
        except Exception:
            return pk
    return pk


def _vehicle_pk(vehicle: Any) -> Any:
    return getattr(vehicle, "id", None) or getattr(vehicle, "vehicle_id", None) or getattr(vehicle, "uuid", None)


def _maybe(vehicle: Any, *names: str) -> Any:
    for n in names:
        if hasattr(vehicle, n):
            return getattr(vehicle, n)
    return None


def _columns(model: Type[Any]) -> dict[str, Any]:
    try:
        return {c.name: c for c in model.__table__.columns}  # type: ignore[attr-defined]
    except Exception:
        return {}


def _set_if_present(kwargs: dict[str, Any], cols: dict[str, Any], names: tuple[str, ...], value: Any) -> bool:
    for n in names:
        if n in cols:
            kwargs[n] = value
            return True
    return False


class VehicleCreateIn(BaseModel):
    vin: str = Field(..., min_length=11, max_length=17)
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1886, le=2100)
    nickname: Optional[str] = None


class VehicleOut(BaseModel):
    id: str
    vin_masked: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    nickname: Optional[str] = None
    servicebook_id: Optional[str] = None


router = APIRouter(prefix="/vehicles", tags=["vehicles"], dependencies=[Depends(forbid_moderator)])



def require_consent(db: Session, actor: Any) -> None:
    """
    Consent-Gate (SoT D-010): blockiert Produkt-Flow ohne gültige Pflicht-Consents.
    - bevorzugt DB-basiert via app.services.consent_store.has_required_consents(db, user_id)
    - fallback via app.consent_store wrapper (env_consent_version/get_consent_status)
    Deny-by-default: wenn Prüfung nicht möglich oder nicht erfüllt -> 403 consent_required.
    """
    uid = _actor_id(actor)
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    uid_s = str(uid)

    # primary: services/consent_store.py
    try:
        from app.services.consent_store import has_required_consents  # type: ignore
        if has_required_consents(db, uid_s):
            return
    except Exception:
        pass

    # fallback: app.consent_store wrapper (db_path + version)
    try:
        import app.consent_store as cs  # type: ignore
        required_version = cs.env_consent_version()
        st = cs.get_consent_status(cs.env_db_path(), uid_s, required_version)
        ok = False
        if isinstance(st, dict):
            ok = bool(st.get("ok") or st.get("has_required") or st.get("accepted"))
        else:
            ok = bool(getattr(st, "ok", False) or getattr(st, "has_required", False) or getattr(st, "accepted", False))
        if ok:
            return
    except Exception:
        pass

    # deny (try include consent_version if available)
    try:
        import app.consent_store as cs  # type: ignore
        v = cs.env_consent_version()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "consent_required", "consent_version": v})
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "consent_required"})
def _enforce_role(actor: Any) -> str:
    role = _role_of(actor)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return role


def _ensure_servicebook_if_needed(db: Session, actor: Any, vehicle: Any) -> None:
    if not hasattr(vehicle, "servicebook_id"):
        return
    if getattr(vehicle, "servicebook_id", None):
        return

    Servicebook = _get_servicebook_model()
    if Servicebook is None:
        return

    sb_cols = _columns(Servicebook)
    sb_kwargs: dict[str, Any] = {}

    vid = _vehicle_pk(vehicle)
    _set_if_present(sb_kwargs, sb_cols, ("vehicle_id",), vid)
    _set_if_present(sb_kwargs, sb_cols, ("vehicle_uuid",), vid)

    aid = _actor_id(actor)
    _set_if_present(sb_kwargs, sb_cols, ("owner_user_id", "owner_id", "user_id", "created_by_user_id"), aid)

    if "created_at" in sb_cols and sb_cols["created_at"].default is None and sb_cols["created_at"].server_default is None:
        sb_kwargs["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

    sb = Servicebook(**sb_kwargs)
    db.add(sb)
    db.commit()
    db.refresh(sb)

    sbid = getattr(sb, "id", None) or getattr(sb, "servicebook_id", None)
    if sbid is not None:
        setattr(vehicle, "servicebook_id", sbid)
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)


def _to_out(vehicle: Any) -> VehicleOut:
    vid = _vehicle_pk(vehicle)
    vin = _maybe(vehicle, "vin", "vin_raw", "vin_full") or ""
    return VehicleOut(
        id=str(vid),
        vin_masked=_mask_vin(str(vin)),
        make=_maybe(vehicle, "make", "brand", "manufacturer"),
        model=_maybe(vehicle, "model", "model_name"),
        year=_maybe(vehicle, "year", "build_year", "model_year"),
        nickname=_maybe(vehicle, "nickname", "display_name", "name"),
        servicebook_id=str(_maybe(vehicle, "servicebook_id")) if _maybe(vehicle, "servicebook_id") is not None else None,
    )


@router.post("", response_model=VehicleOut)
@router.post("/", response_model=VehicleOut)
def create_vehicle(
    payload: VehicleCreateIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleOut:
    role = _enforce_role(actor)
    require_consent(db, actor)
    Vehicle = _get_vehicle_model()

    owner_name, owner_col = _find_owner_col(Vehicle)
    if owner_col is None:
        raise HTTPException(status_code=500, detail="vehicle_owner_field_missing")

    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    if role == "user":
        existing = db.query(Vehicle).filter(owner_col == aid).count()
        if existing >= 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="vehicle_limit_reached")

    vin = _normalize_vin(payload.vin)
    cols = _columns(Vehicle)
    kwargs: dict[str, Any] = {}

    if owner_name and owner_name in cols:
        kwargs[owner_name] = aid

    _set_if_present(kwargs, cols, ("vin", "vin_raw", "vin_full"), vin)
    public_id = uuid.uuid4().hex
    _set_if_present(kwargs, cols, ("public_id", "public_vehicle_id", "public_qr_id", "public_token"), public_id)

    if payload.make:
        _set_if_present(kwargs, cols, ("make", "brand", "manufacturer"), payload.make)
    if payload.model:
        _set_if_present(kwargs, cols, ("model", "model_name"), payload.model)
    if payload.year is not None:
        _set_if_present(kwargs, cols, ("year", "build_year", "model_year"), payload.year)
    if payload.nickname:
        _set_if_present(kwargs, cols, ("nickname", "display_name", "name"), payload.nickname)

    if "created_at" in cols and cols["created_at"].default is None and cols["created_at"].server_default is None:
        kwargs["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

    v = Vehicle(**kwargs)
    db.add(v)
    db.commit()
    db.refresh(v)

    _ensure_servicebook_if_needed(db, actor, v)
    return _to_out(v)


@router.get("", response_model=list[VehicleOut])
@router.get("/", response_model=list[VehicleOut])
def list_vehicles(
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> list[VehicleOut]:
    role = _enforce_role(actor)
    require_consent(db, actor)
    Vehicle = _get_vehicle_model()
    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    owner_name, owner_col = _find_owner_col(Vehicle)
    if owner_col is None:
        raise HTTPException(status_code=500, detail="vehicle_owner_field_missing")

    q = db.query(Vehicle)

    if role not in {"admin", "superadmin"}:
        q = q.filter(owner_col == aid)

    cols = _columns(Vehicle)
    if "created_at" in cols and hasattr(Vehicle, "created_at"):
        q = q.order_by(getattr(Vehicle, "created_at").desc())  # type: ignore[attr-defined]

    return [_to_out(v) for v in q.all()]


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleOut:
    role = _enforce_role(actor)
    require_consent(db, actor)
    Vehicle = _get_vehicle_model()
    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    pk = _coerce_pk(vehicle_id)

    v = None
    try:
        v = db.get(Vehicle, pk)  # type: ignore[attr-defined]
    except Exception:
        if hasattr(Vehicle, "id"):
            v = db.query(Vehicle).filter(getattr(Vehicle, "id") == pk).first()  # type: ignore[attr-defined]

    if v is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if role in {"admin", "superadmin"}:
        return _to_out(v)

    owner_name, _ = _find_owner_col(Vehicle)
    if owner_name and hasattr(v, owner_name):
        if getattr(v, owner_name) != aid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return _to_out(v)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
