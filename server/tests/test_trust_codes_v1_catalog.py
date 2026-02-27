# server/tests/test_trust_codes_v1_catalog.py
from app.services.trust_codes_v1 import validate_catalog, sorted_reasons, vip_top_reasons


def test_trust_codes_catalog_is_valid():
    ok, msg = validate_catalog()
    assert ok, msg


def test_sorted_reasons_is_deterministic():
    codes = [
        "entry_required_fields_missing",
        "public_evidence_incomplete",
        "document_quarantined_not_approved",
    ]
    res = sorted_reasons(codes)
    assert [r.code for r in res] == [
        "public_evidence_incomplete",
        "document_quarantined_not_approved",
        "entry_required_fields_missing",
    ]


def test_vip_top3():
    codes = [
        "entry_required_fields_missing",
        "public_evidence_incomplete",
        "document_quarantined_not_approved",
        "accident_status_unknown_cap_orange",
    ]
    top = vip_top_reasons(codes, top_n=3)
    assert len(top) == 3
    assert [r.code for r in top] == [
        "public_evidence_incomplete",
        "document_quarantined_not_approved",
        "accident_status_unknown_cap_orange",
    ]