from __future__ import annotations

import pytest

from app.services.consent_store import (
    ConsentContractError,
    ensure_required_consents,
    validate_and_normalize_consents,
)


def test_rejects_source_web():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "web"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    with pytest.raises(ConsentContractError):
        validate_and_normalize_consents(consents)


def test_requires_accepted_at():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    with pytest.raises(ConsentContractError):
        validate_and_normalize_consents(consents)


def test_requires_exact_current_versions():
    consents = [
        {"doc_type": "terms", "doc_version": "v2", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    normalized = validate_and_normalize_consents(consents)
    with pytest.raises(ConsentContractError):
        ensure_required_consents(normalized)


def test_accepts_valid_set():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "api"},
    ]
    normalized = validate_and_normalize_consents(consents)
    ensure_required_consents(normalized)