from __future__ import annotations

import datetime as dt
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.guards import forbid_moderator
from app.routers.export_vehicle import get_db, get_actor  # type: ignore
from app.services import servicebook_store


router = APIRouter(prefix="/servicebook", tags=["servicebook"], dependencies=[Depends(forbid_moderator)])


class InspectionEventIn(BaseModel):
    source: Literal["GPS", "READOUT"] = Field(..., description="Interne Quelle (nur Eigenbenutzung)")
    result_status: Literal["OK", "NOT_OK"] = Field(..., description="OK oder Nicht OK")
    title: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    details: Optional[str] = Field(default=None)
    occurred_at: Optional[dt.datetime] = Field(default=None)
    km: Optional[int] = Field(default=None, ge=0)
    document_ids: Optional[List[str]] = Field(default=None, description="Dokument-IDs (Uploads/Quarantine)")


class RemediationIn(BaseModel):
    result_status: Literal["OK", "NOT_OK"] = Field(..., description="Nach Behebung OK oder weiterhin Nicht OK")
    title: Optional[str] = Field(default="Behebung")
    summary: Optional[str] = Field(default=None)
    details: Optional[str] = Field(default=None)
    occurred_at: Optional[dt.datetime] = Field(default=None)
    km: Optional[int] = Field(default=None, ge=0)
    document_ids: Optional[List[str]] = Field(default=None)


def _require_authenticated(actor: Any) -> None:
    if actor is None:
        raise HTTPException(status_code=401, detail="unauthorized")


def _enforce_scope(db: Session, actor: Any, servicebook_id: str) -> None:
    rows = servicebook_store.fetch_entries(db, servicebook_id)
    servicebook_store.enforce_scope_or_admin(actor, rows)


@router.get("/{servicebook_id}/entries")
def list_entries(
    servicebook_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    _require_authenticated(actor)
    _enforce_scope(db, actor, servicebook_id)

    rows = servicebook_store.fetch_entries(db, servicebook_id)
    return {"target": "servicebook", "id": servicebook_id, "entries": rows}


@router.post("/{servicebook_id}/inspection-events")
def create_inspection_event(
    servicebook_id: str,
    payload: InspectionEventIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    """
    Interne Module (GPS/Auslesung):
      - erzeugen Prüf-Event im Serviceheft (OK / NOT_OK)
      - bei NOT_OK: erzeugt automatisch "Case" (Maßnahmenfall) als Entry + Link (best-effort)
    """
    _require_authenticated(actor)

    # Scope check: wenn noch keine Entries existieren => 404; in MVP erlauben wir dann nur admin/superadmin
    try:
        _enforce_scope(db, actor, servicebook_id)
    except HTTPException as e:
        if e.status_code == 404 and servicebook_store.actor_role(actor) in {"admin", "superadmin"}:
            pass
        else:
            raise

    entry = servicebook_store.create_entry(
        db,
        servicebook_id,
        actor,
        entry_type="INSPECTION_EVENT",
        source=payload.source,
        result_status=payload.result_status,
        title=payload.title or f"Prüf-Event ({payload.source})",
        summary=payload.summary,
        details=payload.details,
        occurred_at=payload.occurred_at,
        km=payload.km,
        document_ids=payload.document_ids,
        related_entry_id=None,
        related_case_id=None,
    )

    case_entry = None
    if payload.result_status == "NOT_OK":
        case_entry = servicebook_store.create_entry(
            db,
            servicebook_id,
            actor,
            entry_type="CASE",
            source=payload.source,
            result_status="IN_PROGRESS",
            title="Maßnahmenfall",
            summary="Nicht OK – weitere Maßnahmen erforderlich",
            details=None,
            occurred_at=payload.occurred_at,
            km=payload.km,
            document_ids=None,
            related_entry_id=str(entry.get("id") or ""),
            related_case_id=None,
        )

        # best-effort back-link
        if entry.get("id") and case_entry.get("id"):
            servicebook_store.update_entry_best_effort(
                db,
                str(entry["id"]),
                {
                    "related_case_id": str(case_entry["id"]),
                    "case_id": str(case_entry["id"]),
                    "ref_case_id": str(case_entry["id"]),
                },
            )

    return {"target": "servicebook", "id": servicebook_id, "inspection_event": entry, "case": case_entry}


@router.post("/{servicebook_id}/cases/{case_entry_id}/remediation")
def close_case_with_remediation(
    servicebook_id: str,
    case_entry_id: str,
    payload: RemediationIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    """
    Dokumentiert die Behebung und setzt den Case-Status:
      - OK -> DONE
      - NOT_OK -> IN_PROGRESS
    """
    _require_authenticated(actor)
    _enforce_scope(db, actor, servicebook_id)

    rows = servicebook_store.fetch_entries(db, servicebook_id)
    case_row = None
    for r in rows:
        if str(r.get("id")) == str(case_entry_id):
            case_row = r
            break
    if not case_row:
        raise HTTPException(status_code=404, detail="case_not_found")

    remediation = servicebook_store.create_entry(
        db,
        servicebook_id,
        actor,
        entry_type="REMEDIATION",
        source="OWNER",
        result_status=payload.result_status,
        title=payload.title or "Behebung",
        summary=payload.summary,
        details=payload.details,
        occurred_at=payload.occurred_at,
        km=payload.km,
        document_ids=payload.document_ids,
        related_entry_id=str(case_row.get("id") or ""),
        related_case_id=str(case_row.get("id") or ""),
    )

    new_case_status = "DONE" if payload.result_status == "OK" else "IN_PROGRESS"
    servicebook_store.update_entry_best_effort(
        db,
        str(case_entry_id),
        {
            "result_status": new_case_status,
            "status": new_case_status,
            "result": new_case_status,
            "closing_entry_id": str(remediation.get("id") or ""),
            "related_entry_id": str(remediation.get("id") or ""),
        },
    )

    return {
        "target": "servicebook",
        "id": servicebook_id,
        "case_id": case_entry_id,
        "remediation": remediation,
        "case_status": new_case_status,
    }
