from __future__ import annotations

from typing import Final

DOC_TERMS: Final[str] = "terms"
DOC_PRIVACY: Final[str] = "privacy"

SOURCE_UI: Final[str] = "ui"
SOURCE_API: Final[str] = "api"

# Single Source of Truth: required consent documents and their current versions.
CURRENT_DOC_VERSIONS: Final[dict[str, str]] = {
    DOC_TERMS: "v1",
    DOC_PRIVACY: "v1",
}

ALLOWED_DOC_TYPES: Final[frozenset[str]] = frozenset(CURRENT_DOC_VERSIONS.keys())
ALLOWED_SOURCES: Final[frozenset[str]] = frozenset({SOURCE_UI, SOURCE_API})


def required_consents() -> list[dict[str, str]]:
    return [{"doc_type": dt, "doc_version": ver} for dt, ver in CURRENT_DOC_VERSIONS.items()]