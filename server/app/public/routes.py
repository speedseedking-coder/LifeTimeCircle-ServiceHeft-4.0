# C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server\app\public\routes.py

from __future__ import annotations

from fastapi import APIRouter, Depends
from app.guards import forbid_moderator
from pydantic import BaseModel, Field



from app.services.trust_light_v1 import (
    compute_public_hint_from_reason_codes,
    compute_trust_light_from_reason_codes,
    green_fallback_hint,
)
router = APIRouter(dependencies=[Depends(forbid_moderator)], prefix="/public", tags=["public"])


DISCLAIMER_TEXT = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

class PublicQrResponse(BaseModel):
    trust_light: str = Field(..., description="rot|orange|gelb|gruen")
    hint: str = Field(..., description="Kurzer Hinweis ohne Metriken/Zahlen/Zeiträume")
    disclaimer: str = Field(..., description="Pflicht-Disclaimer für Public-QR")


@router.get("/qr/{vehicle_id}", response_model=PublicQrResponse)
def get_public_qr(vehicle_id: str) -> PublicQrResponse:
    """
    Public-QR: nur Doku-/Nachweisqualität, NIE technischer Zustand.
    Keine Metrics/Counts/Percentages/Zeiträume in der Response.
    """

    # Minimaler, policy-konformer Start (später: echte Ableitung aus Einträgen/Belegen/T-Level).
    # Hinweistext absichtlich ohne Zahlen/Zeiträume.
    codes = ["public_evidence_incomplete"]

    trust_light = compute_trust_light_from_reason_codes(codes)
    hint = compute_public_hint_from_reason_codes(codes) or green_fallback_hint()
    return PublicQrResponse(trust_light=trust_light, hint=hint, disclaimer=DISCLAIMER_TEXT)
