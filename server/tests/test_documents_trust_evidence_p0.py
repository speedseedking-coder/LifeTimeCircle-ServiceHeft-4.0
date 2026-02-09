# server/tests/test_documents_trust_evidence_p0.py
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models.documents import (
    Document,
    DocumentApprovalStatus,
    DocumentPiiStatus,
    DocumentScanStatus,
)
from app.services.documents_service import (
    approve_document,
    is_valid_trust_evidence,
    mark_pii_status,
    reject_document,
    set_scan_status,
)
from app.services.trust_evidence_service import get_trust_evidence_for_vehicle

from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def mk_doc(vehicle_id: int, created_by_user_id: int) -> Document:
    return Document(
        vehicle_id=vehicle_id,
        created_by_user_id=created_by_user_id,
        filename="a.pdf",
        content_type="application/pdf",
        size_bytes=123,
        storage_key="k",
        checksum_sha256="0" * 64,
        approval_status=DocumentApprovalStatus.QUARANTINED,
        scan_status=DocumentScanStatus.PENDING,
        pii_status=DocumentPiiStatus.OK,
    )


def test_upload_default_is_quarantined_pending(db: Session):
    d = mk_doc(vehicle_id=1, created_by_user_id=10)
    db.add(d)
    db.commit()
    db.refresh(d)

    assert d.approval_status == DocumentApprovalStatus.QUARANTINED
    assert d.scan_status == DocumentScanStatus.PENDING
    assert d.pii_status == DocumentPiiStatus.OK
    assert len(d.checksum_sha256) == 64


def test_approve_requires_clean_and_pii_ok(db: Session):
    d = mk_doc(vehicle_id=1, created_by_user_id=10)
    db.add(d)
    db.commit()
    db.refresh(d)

    with pytest.raises(HTTPException) as e1:
        approve_document(d, admin_user_id=1)
    assert e1.value.status_code == 409
    assert e1.value.detail == "scan_not_clean"

    set_scan_status(d, DocumentScanStatus.CLEAN, admin_user_id=1)
    mark_pii_status(d, DocumentPiiStatus.SUSPECTED, marker_user_id=10, note="pii?")
    with pytest.raises(HTTPException) as e2:
        approve_document(d, admin_user_id=1)
    assert e2.value.status_code == 409
    assert e2.value.detail == "pii_not_cleared"

    mark_pii_status(d, DocumentPiiStatus.OK, marker_user_id=1, note="cleared")
    approve_document(d, admin_user_id=1)
    assert d.approval_status == DocumentApprovalStatus.APPROVED
    assert d.approved_by_user_id == 1
    assert d.approved_at is not None


def test_infected_auto_reject(db: Session):
    d = mk_doc(vehicle_id=1, created_by_user_id=10)
    db.add(d)
    db.commit()
    db.refresh(d)

    set_scan_status(d, DocumentScanStatus.INFECTED, admin_user_id=99)
    assert d.scan_status == DocumentScanStatus.INFECTED
    assert d.approval_status == DocumentApprovalStatus.REJECTED
    assert d.reject_reason == "infected_auto_reject"


def test_valid_trust_evidence_definition(db: Session):
    d = mk_doc(vehicle_id=1, created_by_user_id=10)
    db.add(d)
    db.commit()
    db.refresh(d)

    assert not is_valid_trust_evidence(d)

    set_scan_status(d, DocumentScanStatus.CLEAN, admin_user_id=1)
    mark_pii_status(d, DocumentPiiStatus.OK, marker_user_id=1, note=None)
    approve_document(d, admin_user_id=1)

    assert is_valid_trust_evidence(d)

    # if pii becomes suspected later, it must stop being valid evidence
    mark_pii_status(d, DocumentPiiStatus.SUSPECTED, marker_user_id=10, note="oops")
    assert not is_valid_trust_evidence(d)


def test_trust_evidence_service_separates_valid_and_blocked(db: Session):
    d1 = mk_doc(vehicle_id=1, created_by_user_id=10)
    d2 = mk_doc(vehicle_id=1, created_by_user_id=10)
    d3 = mk_doc(vehicle_id=2, created_by_user_id=10)

    # make d2 valid
    set_scan_status(d2, DocumentScanStatus.CLEAN, admin_user_id=1)
    approve_document(d2, admin_user_id=1)

    db.add(d1)
    db.add(d2)
    db.add(d3)
    db.commit()

    ev = get_trust_evidence_for_vehicle(db, vehicle_id=1)
    assert ev.valid_count == 1
    assert ev.blocked_count == 1