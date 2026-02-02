from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.consent.policy import required_consents
from app.deps import get_db
from app.guards import forbid_moderator
from app.rbac import get_current_user
from app.services.consent_store import (
    ConsentContractError,
    ensure_required_consents,
    get_user_consents,
    record_consents,
    validate_and_normalize_consents,
)

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentItem(BaseModel):
    doc_type: str
    doc_version: str
    accepted_at: str
    source: str


class ConsentAcceptRequest(BaseModel):
    consents: list[ConsentItem] = Field(default_factory=list)


def _dump_model(m: BaseModel) -> dict[str, Any]:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()


def _user_id_from_current_user(user: Any) -> str:
    """
    get_current_user liefert im Projekt teils ein dict (z.B. {"user_id": "...", "role": ...})
    oder ein Objekt mit Attribut .id. Beides wird unterstützt.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    if hasattr(user, "id") and getattr(user, "id") is not None:
        return str(getattr(user, "id"))

    if isinstance(user, dict):
        for key in ("id", "user_id", "sub"):
            v = user.get(key)
            if v:
                return str(v)

    raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/current")
def consent_current():
    # public discovery endpoint (no auth)
    return {"required": required_consents()}


@router.get("/status", dependencies=[Depends(forbid_moderator)])
def consent_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    uid = _user_id_from_current_user(user)
    accepted = get_user_consents(db, uid)
    required = required_consents()
    have = {(a["doc_type"], a["doc_version"]) for a in accepted}
    is_complete = all((r["doc_type"], r["doc_version"]) in have for r in required)
    return {"required": required, "accepted": accepted, "is_complete": is_complete}


@router.post("/accept", dependencies=[Depends(forbid_moderator)])
def consent_accept(payload: ConsentAcceptRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    uid = _user_id_from_current_user(user)

    try:
        raw = [_dump_model(x) for x in payload.consents]
        normalized = validate_and_normalize_consents(raw)
        ensure_required_consents(normalized)
        record_consents(db, uid, normalized)
        return {"ok": True}
    except ConsentContractError as e:
        raise HTTPException(status_code=400, detail=str(e))