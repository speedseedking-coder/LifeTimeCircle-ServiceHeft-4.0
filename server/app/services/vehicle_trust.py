from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Optional

from app.models.vehicle_entry import VehicleEntry
from app.services.trust_codes_v1 import vip_top_reasons
from app.services.trust_light_v1 import (
    compute_public_hint_from_reason_codes,
    compute_trust_light_from_reason_codes,
    green_fallback_hint,
)

AccidentStatus = Literal["unfallfrei", "nicht_unfallfrei", "unbekannt"]
VerificationLevel = Literal["niedrig", "mittel", "hoch"]
PresenceLabel = Literal["vorhanden", "nicht_vorhanden"]


@dataclass(frozen=True)
class VehicleTrustSummary:
    trust_light: str
    hint: str
    reason_codes: list[str]
    todo_codes: list[str]
    verification_level: VerificationLevel
    accident_status: AccidentStatus
    history_status: PresenceLabel
    evidence_status: PresenceLabel
    top_trust_level: Optional[str]


def _meta_value(meta: Optional[dict[str, Any]], key: str, default: Any = None) -> Any:
    if not isinstance(meta, dict):
        return default
    return meta.get(key, default)


def normalize_accident_status(meta: Optional[dict[str, Any]]) -> AccidentStatus:
    raw = str(_meta_value(meta, "accident_status", "unknown") or "unknown").strip().lower()
    mapping = {
        "unfallfrei": "unfallfrei",
        "accident_free": "unfallfrei",
        "free": "unfallfrei",
        "none": "unfallfrei",
        "nicht_unfallfrei": "nicht_unfallfrei",
        "not_free": "nicht_unfallfrei",
        "accident": "nicht_unfallfrei",
        "not_accident_free": "nicht_unfallfrei",
        "unbekannt": "unbekannt",
        "unknown": "unbekannt",
    }
    return mapping.get(raw, "unbekannt")


def accident_status_public_label(status: AccidentStatus) -> str:
    if status == "unfallfrei":
        return "Unfallfrei"
    if status == "nicht_unfallfrei":
        return "Nicht unfallfrei"
    return "Unbekannt"


def _top_trust_level(entries: Iterable[VehicleEntry]) -> Optional[str]:
    levels = {str(entry.trust_level or "").strip().upper() for entry in entries}
    if "T3" in levels:
        return "T3"
    if "T2" in levels:
        return "T2"
    if "T1" in levels:
        return "T1"
    return None


def _verification_level(top_trust_level: Optional[str]) -> VerificationLevel:
    if top_trust_level == "T3":
        return "hoch"
    if top_trust_level == "T2":
        return "mittel"
    return "niedrig"


def _evidence_status(top_trust_level: Optional[str]) -> PresenceLabel:
    if top_trust_level in {"T2", "T3"}:
        return "vorhanden"
    return "nicht_vorhanden"


def derive_vehicle_trust_summary(
    *,
    vehicle_meta: Optional[dict[str, Any]],
    entries: Iterable[VehicleEntry],
) -> VehicleTrustSummary:
    latest_entries = list(entries)
    accident_status = normalize_accident_status(vehicle_meta)
    top_trust_level = _top_trust_level(latest_entries)
    verification_level = _verification_level(top_trust_level)
    history_status: PresenceLabel = "vorhanden" if latest_entries else "nicht_vorhanden"
    evidence_status = _evidence_status(top_trust_level)

    reason_codes: list[str] = []
    if not latest_entries:
        reason_codes.append("public_evidence_incomplete")
    elif top_trust_level == "T2":
        reason_codes.append("t3_requires_document_missing")
    elif top_trust_level in {None, "T1"}:
        reason_codes.append("t1_physical_servicebook_not_present")

    if accident_status == "unbekannt":
        reason_codes.append("accident_status_unknown_cap_orange")
    elif accident_status == "nicht_unfallfrei":
        accident_trust_completed = bool(_meta_value(vehicle_meta, "accident_trust_completed", False))
        if not accident_trust_completed:
            reason_codes.append("accident_not_free_requires_completed_accident_trust")
        elif top_trust_level != "T3":
            reason_codes.append("accident_trust_missing_evidence")

    trust_light = compute_trust_light_from_reason_codes(reason_codes)
    hint = compute_public_hint_from_reason_codes(reason_codes) or green_fallback_hint()
    todo_codes = [reason.code for reason in vip_top_reasons(reason_codes)]

    return VehicleTrustSummary(
        trust_light=trust_light,
        hint=hint,
        reason_codes=reason_codes,
        todo_codes=todo_codes,
        verification_level=verification_level,
        accident_status=accident_status,
        history_status=history_status,
        evidence_status=evidence_status,
        top_trust_level=top_trust_level,
    )
