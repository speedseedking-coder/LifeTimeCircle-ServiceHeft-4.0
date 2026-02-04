# server/tests/test_export_servicebook_redaction_approved_only.py
from __future__ import annotations

from copy import deepcopy

from app.services.export_servicebook_redaction import redact_servicebook_export


def test_redacted_export_includes_only_approved_doc_refs_everywhere() -> None:
    export_obj = {
        "servicebook": {"id": "sb_1"},
        "documents": [
            {"doc_id": "d_ok", "status": "APPROVED", "title": "OK"},
            {"doc_id": "d_pending", "status": "PENDING", "title": "P"},
            {"doc_id": "d_rejected", "status": "REJECTED", "title": "R"},
            {"doc_id": "d_missing_status", "title": "M"},
        ],
        "entries": [
            {
                "id": "e1",
                "title": "Entry 1",
                "doc_id": "d_ok",
                "document_ids": ["d_ok", "d_pending", "d_rejected", "d_missing_status", None, ""],
                "documents": [
                    {"doc_id": "d_ok", "status": "APPROVED"},
                    {"doc_id": "d_pending", "status": "PENDING"},
                    {"doc_id": "d_rejected", "status": "REJECTED"},
                    {"doc_id": "d_missing_status"},
                ],
            },
            {
                "id": "e2",
                "title": "Entry 2",
                "attachments": ["d_ok", "d_pending", "nope", ""],
            },
        ],
        "nested": {
            "foo": {
                "document_id": "d_pending",
                "bar": [{"documentId": "d_ok"}, {"documentId": "d_rejected"}],
            }
        },
    }

    src = deepcopy(export_obj)
    redacted = redact_servicebook_export(src)

    # Top-Level documents: nur APPROVED
    assert isinstance(redacted["documents"], list)
    assert [d["doc_id"] for d in redacted["documents"]] == ["d_ok"]

    # Entry 1: nur APPROVED refs
    e1 = redacted["entries"][0]
    assert e1.get("doc_id") == "d_ok"
    assert e1.get("document_ids") == ["d_ok"]
    assert [d.get("doc_id") for d in e1.get("documents", [])] == ["d_ok"]

    # Entry 2: attachments nur APPROVED
    e2 = redacted["entries"][1]
    assert e2.get("attachments") == ["d_ok"]

    # Nested: pending/rejected refs entfernt
    assert "document_id" not in redacted["nested"]["foo"]
    assert redacted["nested"]["foo"]["bar"] == [{"documentId": "d_ok"}]


def test_redacted_export_without_top_level_documents_denies_all_doc_refs() -> None:
    export_obj = {
        "servicebook": {"id": "sb_1"},
        # absichtlich KEIN "documents" Top-Level
        "entries": [
            {
                "id": "e1",
                "doc_id": "d_any",
                "document_ids": ["d_any", "d_other"],
                "documents": [{"doc_id": "d_any", "status": "APPROVED"}],
                "attachments": ["d_any"],
            }
        ],
    }

    redacted = redact_servicebook_export(deepcopy(export_obj))

    e1 = redacted["entries"][0]
    assert "doc_id" not in e1
    assert e1.get("document_ids") == []
    assert e1.get("documents") == []
    assert e1.get("attachments") == []
