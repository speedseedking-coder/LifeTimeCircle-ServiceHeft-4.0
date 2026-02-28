# C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server\app\public\routes.py

from __future__ import annotations

from fastapi import APIRouter, Depends
from app.guards import forbid_moderator
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from app.deps import get_db  # type: ignore
except Exception:  # pragma: no cover
    from app.db.session import get_db  # type: ignore

from app.models.vehicle import Vehicle
from app.models.vehicle_entry import VehicleEntry
from app.services.vehicle_trust import (
    accident_status_public_label,
    derive_vehicle_trust_summary,
)

from app.services.trust_light_v1 import (
    green_fallback_hint,
)
router = APIRouter(dependencies=[Depends(forbid_moderator)], prefix="/public", tags=["public"])


DISCLAIMER_TEXT = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

class PublicQrResponse(BaseModel):
    trust_light: str = Field(..., description="rot|orange|gelb|gruen")
    hint: str = Field(..., description="Kurzer Hinweis ohne Metriken/Zahlen/Zeiträume")
    history_status: str = Field(..., description="vorhanden|nicht_vorhanden")
    evidence_status: str = Field(..., description="vorhanden|nicht_vorhanden")
    verification_level: str = Field(..., description="niedrig|mittel|hoch")
    accident_status: str = Field(..., description="unfallfrei|nicht_unfallfrei|unbekannt")
    accident_status_label: str = Field(..., description="Öffentliche Badge-Kopie")
    disclaimer: str = Field(..., description="Pflicht-Disclaimer für Public-QR")


@router.get("/qr/{vehicle_id}", response_model=PublicQrResponse)
def get_public_qr(vehicle_id: str, db: Session = Depends(get_db)) -> PublicQrResponse:
    """
    Public-QR: nur Doku-/Nachweisqualität, NIE technischer Zustand.
    Keine Metrics/Counts/Percentages/Zeiträume in der Response.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.public_id == str(vehicle_id)).first()
    if vehicle is None:
        summary = derive_vehicle_trust_summary(vehicle_meta=None, entries=[])
    else:
        entries = (
            db.query(VehicleEntry)
            .filter(VehicleEntry.vehicle_id == vehicle.public_id, VehicleEntry.is_latest.is_(True))
            .order_by(VehicleEntry.entry_date.desc(), VehicleEntry.created_at.desc())
            .all()
        )
        summary = derive_vehicle_trust_summary(vehicle_meta=vehicle.meta, entries=entries)

    hint = summary.hint or green_fallback_hint()
    return PublicQrResponse(
        trust_light=summary.trust_light,
        hint=hint,
        history_status=summary.history_status,
        evidence_status=summary.evidence_status,
        verification_level=summary.verification_level,
        accident_status=summary.accident_status,
        accident_status_label=accident_status_public_label(summary.accident_status),
        disclaimer=DISCLAIMER_TEXT,
    )
