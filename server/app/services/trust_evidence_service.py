# server/app/services/trust_evidence_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlmodel import Session, select

from app.models.documents import Document
from app.services.documents_service import is_valid_trust_evidence


@dataclass(frozen=True)
class TrustEvidence:
    valid_documents: List[Document]
    blocked_documents: List[Document]

    @property
    def valid_count(self) -> int:
        return len(self.valid_documents)

    @property
    def blocked_count(self) -> int:
        return len(self.blocked_documents)


def get_trust_evidence_for_vehicle(db: Session, vehicle_id: int) -> TrustEvidence:
    docs = list(db.exec(select(Document).where(Document.vehicle_id == vehicle_id)))
    valid = [d for d in docs if is_valid_trust_evidence(d)]
    blocked = [d for d in docs if not is_valid_trust_evidence(d)]
    return TrustEvidence(valid_documents=valid, blocked_documents=blocked)