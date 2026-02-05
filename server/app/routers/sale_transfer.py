from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import Actor, require_roles
from app.db.session import get_db
from app.guards import forbid_moderator
from app.services.sale_transfer_store import (
    cancel_transfer,
    create_transfer,
    get_transfer_status,
    redeem_transfer,
)

router = APIRouter(
    prefix="/sale/transfer",
    tags=["sale_transfer"],
    dependencies=[Depends(forbid_moderator)],
)


def _actor_user_id(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("user_id") or actor.get("id") or actor.get("subject_id") or actor.get("sub") or "")
    for key in ("user_id", "id", "subject_id", "sub"):
        v = getattr(actor, key, None)
        if v:
            return str(v)
    return ""


def _actor_role(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return str(getattr(actor, "role", "") or "")


class SaleTransferCreateIn(BaseModel):
    vehicle_id: str = Field(min_length=1, max_length=128)
    ttl_seconds: Optional[int] = Field(default=None, ge=60, le=7 * 24 * 3600)


class SaleTransferCreateOut(BaseModel):
    transfer_id: str
    transfer_token: str
    expires_at: str  # ISO8601 UTC (Z)
    status: str


class SaleTransferRedeemIn(BaseModel):
    transfer_token: str = Field(min_length=20, max_length=256)


class SaleTransferRedeemOut(BaseModel):
    transfer_id: str
    vehicle_id: str
    status: str
    ownership_transferred: bool


class SaleTransferCancelIn(BaseModel):
    transfer_id: str = Field(min_length=1, max_length=64)


class SaleTransferCancelOut(BaseModel):
    ok: bool
    transfer_id: str
    status: str


class SaleTransferStatusOut(BaseModel):
    transfer_id: str
    vehicle_id: str
    status: str
    created_at: str
    expires_at: str
    is_expired: bool
    redeemed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    redeemed_by_user_id: Optional[str] = None
    initiator_user_id: str
    ownership_transferred: bool


@router.post("/create", response_model=SaleTransferCreateOut)
def sale_transfer_create(
    payload: SaleTransferCreateIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferCreateOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = create_transfer(
        db=db,
        initiator_user_id=uid,
        initiator_role=role,
        vehicle_id=payload.vehicle_id,
        ttl_seconds=payload.ttl_seconds,
    )
    return SaleTransferCreateOut(**out)


@router.post("/redeem", response_model=SaleTransferRedeemOut)
def sale_transfer_redeem(
    payload: SaleTransferRedeemIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferRedeemOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = redeem_transfer(
        db=db,
        redeemer_user_id=uid,
        redeemer_role=role,
        transfer_token=payload.transfer_token,
    )
    return SaleTransferRedeemOut(**out)


@router.post("/cancel", response_model=SaleTransferCancelOut)
def sale_transfer_cancel(
    payload: SaleTransferCancelIn,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferCancelOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = cancel_transfer(
        db=db,
        initiator_user_id=uid,
        initiator_role=role,
        transfer_id=payload.transfer_id,
    )
    return SaleTransferCancelOut(**out)


@router.get("/status/{transfer_id}", response_model=SaleTransferStatusOut)
def sale_transfer_status(
    transfer_id: str,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("vip", "dealer"))],
) -> SaleTransferStatusOut:
    uid = _actor_user_id(actor)
    role = _actor_role(actor)
    if not uid or role not in {"vip", "dealer", "admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")
    out = get_transfer_status(
        db=db,
        actor_user_id=uid,
        actor_role=role,
        transfer_id=transfer_id,
    )
    return SaleTransferStatusOut(**out)