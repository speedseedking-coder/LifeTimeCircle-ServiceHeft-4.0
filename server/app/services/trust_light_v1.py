# server/app/services/trust_light_v1.py
# Mapping Reason-Codes -> trust_light (rot|orange|gelb|gruen), deterministisch.
# block -> rot, cap -> orange, warn -> gelb, none -> gruen

from __future__ import annotations

from typing import List, Literal, Optional

from app.services.trust_codes_v1 import sorted_reasons

TrustLight = Literal["rot", "orange", "gelb", "gruen"]


def compute_trust_light_from_reason_codes(codes: List[str]) -> TrustLight:
    reasons = sorted_reasons(codes)
    if not reasons:
        return "gruen"

    severities = {r.severity for r in reasons}
    if "block" in severities:
        return "rot"
    if "cap" in severities:
        return "orange"
    return "gelb"


def compute_public_hint_from_reason_codes(codes: List[str]) -> Optional[str]:
    reasons = sorted_reasons(codes)
    return reasons[0].hint if reasons else None


def green_fallback_hint() -> str:
    return "Dokumentation ist vollständig nachweisbar."