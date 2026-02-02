from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consent.policy import (
    ALLOWED_DOC_TYPES,
    ALLOWED_SOURCES,
    CURRENT_DOC_VERSIONS,
    required_consents,
)
from app.models.consent import ConsentAcceptance


class ConsentContractError(ValueError):
    pass


def _parse_iso8601_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ConsentContractError("accepted_at muss ISO8601 string sein")

    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception as e:
        raise ConsentContractError("accepted_at ist kein gültiger ISO8601 Zeitstempel") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_and_normalize_consents(consents: Any) -> list[dict[str, Any]]:
    if consents is None:
        return []
    if not isinstance(consents, list):
        raise ConsentContractError("consents muss eine Liste sein")

    out: list[dict[str, Any]] = []
    seen_types: set[str] = set()

    for i, item in enumerate(consents):
        if not isinstance(item, dict):
            raise ConsentContractError(f"consents[{i}] muss ein Objekt sein")

        doc_type = item.get("doc_type")
        doc_version = item.get("doc_version")
        accepted_at = item.get("accepted_at")
        source = item.get("source")

        if doc_type not in ALLOWED_DOC_TYPES:
            raise ConsentContractError(f"consents[{i}].doc_type ungültig")
        if not isinstance(doc_version, str) or not doc_version.strip():
            raise ConsentContractError(f"consents[{i}].doc_version fehlt")
        if source not in ALLOWED_SOURCES:
            raise ConsentContractError(f"consents[{i}].source muss ui oder api sein")
        if accepted_at is None:
            raise ConsentContractError(f"consents[{i}].accepted_at fehlt")

        dt = _parse_iso8601_utc(str(accepted_at))

        if doc_type in seen_types:
            raise ConsentContractError(f"doc_type doppelt: {doc_type}")
        seen_types.add(doc_type)

        out.append(
            {
                "doc_type": doc_type,
                "doc_version": doc_version.strip(),
                "accepted_at": dt,
                "source": source,
            }
        )

    return out


def ensure_required_consents(normalized: list[dict[str, Any]]) -> None:
    by_type = {c["doc_type"]: c for c in normalized}
    missing: list[str] = []

    for doc_type, required_ver in CURRENT_DOC_VERSIONS.items():
        got = by_type.get(doc_type)
        if got is None or got.get("doc_version") != required_ver:
            missing.append(f"{doc_type}:{required_ver}")

    if missing:
        raise ConsentContractError("Pflicht-Consents fehlen oder Version falsch: " + ", ".join(missing))


def record_consents(db: Session, user_id: str, normalized: list[dict[str, Any]]) -> None:
    now = datetime.now(tz=timezone.utc)

    for c in normalized:
        stmt = select(ConsentAcceptance).where(
            ConsentAcceptance.user_id == user_id,
            ConsentAcceptance.doc_type == c["doc_type"],
            ConsentAcceptance.doc_version == c["doc_version"],
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            continue

        db.add(
            ConsentAcceptance(
                user_id=user_id,
                doc_type=c["doc_type"],
                doc_version=c["doc_version"],
                accepted_at=c["accepted_at"],
                source=c["source"],
                created_at=now,
            )
        )

    db.commit()


def get_user_consents(db: Session, user_id: str) -> list[dict[str, Any]]:
    stmt = select(ConsentAcceptance).where(ConsentAcceptance.user_id == user_id)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "doc_type": r.doc_type,
            "doc_version": r.doc_version,
            "accepted_at": r.accepted_at.astimezone(timezone.utc).isoformat(),
            "source": r.source,
        }
        for r in rows
    ]


def has_required_consents(db: Session, user_id: str) -> bool:
    rows = get_user_consents(db, user_id)
    have = {(r["doc_type"], r["doc_version"]) for r in rows}
    for doc_type, ver in CURRENT_DOC_VERSIONS.items():
        if (doc_type, ver) not in have:
            return False
    return True