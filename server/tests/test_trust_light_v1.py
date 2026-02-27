# server/tests/test_trust_light_v1.py
from app.services.trust_light_v1 import (
    compute_public_hint_from_reason_codes,
    compute_trust_light_from_reason_codes,
    green_fallback_hint,
)


def test_trust_light_none_is_gruen():
    assert compute_trust_light_from_reason_codes([]) == "gruen"


def test_trust_light_warn_is_gelb():
    assert compute_trust_light_from_reason_codes(["public_evidence_incomplete"]) == "gelb"


def test_trust_light_cap_is_orange():
    assert compute_trust_light_from_reason_codes(["document_quarantined_not_approved"]) == "orange"


def test_public_hint_is_deterministic_top1():
    hint = compute_public_hint_from_reason_codes(
        ["document_quarantined_not_approved", "public_evidence_incomplete"]
    )
    assert hint == "Dokumentation vorhanden, aber Nachweise sind teilweise unvollständig."


def test_green_fallback_hint_has_no_digits():
    assert not any(ch.isdigit() for ch in green_fallback_hint())