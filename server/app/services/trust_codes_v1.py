# server/app/services/trust_codes_v1.py
# Trust-Ampel v1: deterministische Reason-Codes + Prioritäten (no-PII)
#
# Public-Hint Policy:
# - Keine Ziffern/Metriken/Zeiträume im hint (Validator enforced).
# - Deterministisch sortiert: priority ASC, code ASC.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

ReasonSeverity = Literal["block", "cap", "warn"]

VIP_TOP_N: int = 3


@dataclass(frozen=True)
class TrustReasonDef:
    code: str
    priority: int
    severity: ReasonSeverity
    decision: str
    hint: str  # kurz, no-PII, ohne Ziffern


REASONS: Dict[str, TrustReasonDef] = {
    # Public (v1)
    "public_evidence_incomplete": TrustReasonDef(
        code="public_evidence_incomplete",
        priority=10,
        severity="warn",
        decision="MVP/Public",
        hint="Dokumentation vorhanden, aber Nachweise sind teilweise unvollständig.",
    ),

    # Dokumente/Quarantäne/Approval (D-003/D-004)
    "document_quarantined_not_approved": TrustReasonDef(
        code="document_quarantined_not_approved",
        priority=20,
        severity="cap",
        decision="D-003/D-004",
        hint="Dokumente sind noch nicht freigegeben. Nachweise zählen erst nach Prüfung.",
    ),

    # Unfall / Caps (D-021)
    "accident_status_unknown_cap_orange": TrustReasonDef(
        code="accident_status_unknown_cap_orange",
        priority=30,
        severity="cap",
        decision="D-021",
        hint="Unfallstatus ist unbekannt. Trust ist begrenzt.",
    ),
    "accident_not_free_requires_completed_accident_trust": TrustReasonDef(
        code="accident_not_free_requires_completed_accident_trust",
        priority=40,
        severity="cap",
        decision="D-021",
        hint="Bei Unfall braucht es vollständige Nachweise für eine hohe Trust-Stufe.",
    ),
    "accident_trust_missing_evidence": TrustReasonDef(
        code="accident_trust_missing_evidence",
        priority=50,
        severity="warn",
        decision="D-021",
        hint="Für Unfalltrust fehlen Nachweise für eine belastbare Bewertung.",
    ),

    # PII blockiert T3 (D-013/D-023)
    "pii_suspected_blocks_t3": TrustReasonDef(
        code="pii_suspected_blocks_t3",
        priority=60,
        severity="block",
        decision="D-013/D-023",
        hint="Offene Datenschutz-Prüfung blockiert die höchste Trust-Stufe.",
    ),
    "pii_confirmed_blocks_t3": TrustReasonDef(
        code="pii_confirmed_blocks_t3",
        priority=61,
        severity="block",
        decision="D-013/D-023",
        hint="Datenschutz-Befund blockiert die höchste Trust-Stufe bis zur Bereinigung.",
    ),

    # Tier-Definition (D-020)
    "t3_requires_document_missing": TrustReasonDef(
        code="t3_requires_document_missing",
        priority=70,
        severity="warn",
        decision="D-020",
        hint="Für die höchste Trust-Stufe ist ein Dokument als Nachweis erforderlich.",
    ),
    "t2_requires_physical_servicebook_missing": TrustReasonDef(
        code="t2_requires_physical_servicebook_missing",
        priority=80,
        severity="warn",
        decision="D-020",
        hint="Für eine mittlere Trust-Stufe ist ein physisches Serviceheft erforderlich.",
    ),
    "t1_physical_servicebook_not_present": TrustReasonDef(
        code="t1_physical_servicebook_not_present",
        priority=90,
        severity="warn",
        decision="D-020",
        hint="Ein physisches Serviceheft ist nicht vorhanden. Trust bleibt begrenzt.",
    ),

    # Integrität (D-014)
    "trusted_upload_hash_missing": TrustReasonDef(
        code="trusted_upload_hash_missing",
        priority=100,
        severity="warn",
        decision="D-014",
        hint="Ein Integritätssignal fehlt. Nachweise sind weniger belastbar.",
    ),

    # Pflichtfelder (D-019)
    "entry_required_fields_missing": TrustReasonDef(
        code="entry_required_fields_missing",
        priority=110,
        severity="warn",
        decision="D-019",
        hint="Pflichtangaben fehlen. Dokumentation ist nicht vollständig nachweisbar.",
    ),
}


def sorted_reasons(codes: List[str]) -> List[TrustReasonDef]:
    items: List[TrustReasonDef] = []
    for c in codes:
        r = REASONS.get(c)
        if r is not None:
            items.append(r)
    items.sort(key=lambda r: (r.priority, r.code))
    return items


def vip_top_reasons(codes: List[str], top_n: int = VIP_TOP_N) -> List[TrustReasonDef]:
    return sorted_reasons(codes)[:top_n]


def validate_catalog() -> Tuple[bool, str]:
    seen = set()
    for k, v in REASONS.items():
        if k != v.code:
            return False, f"Key != code: {k} != {v.code}"
        if v.code in seen:
            return False, f"Duplicate code: {v.code}"
        seen.add(v.code)
        if v.priority < 1:
            return False, f"Invalid priority for {v.code}: {v.priority}"
        if " " in v.code:
            return False, f"Whitespace in code: {v.code}"
        if any(ch.isdigit() for ch in v.hint):
            return False, f"Digit in hint for {v.code}"
    return True, "OK"