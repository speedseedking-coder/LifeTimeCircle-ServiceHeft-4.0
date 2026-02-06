from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Tuple

from sqlalchemy.orm import Session as SASession

from app.consent.policy import required_consents
from app.deps import get_db
from app.services.consent_store import (
    ConsentContractError,
    ensure_required_consents,
    get_user_consents,
    record_consents,
    validate_and_normalize_consents,
)

# --------------------------------------------------------------------
# COMPAT LAYER
# auth/routes.py importiert historisch:
#   from app.consent_store import record_consent, get_consent_status, env_consent_version, env_db_path
#
# Source of Truth bleibt:
#   - app/consent/policy.py
#   - app/services/consent_store.py
# --------------------------------------------------------------------


def env_consent_version() -> str:
    # historisch: eine globale Consent-Version
    # aktuell v1 (pro doc weiterhin in policy.py)
    return "v1"


def env_db_path() -> str:
    # historisch: DB-Pfad aus Env oder Default server/data/app.db
    p = os.getenv("LTC_DB_PATH")
    if p:
        return p
    server_root = Path(__file__).resolve().parents[1]  # .../server
    return str(server_root / "data" / "app.db")


def _coerce_consents(consents: Any) -> list[dict[str, Any]]:
    if consents is None:
        return []
    if not isinstance(consents, list):
        raise ConsentContractError("consents muss eine Liste sein")

    out: list[dict[str, Any]] = []
    for item in consents:
        if isinstance(item, dict):
            out.append(item)
        elif hasattr(item, "model_dump"):
            out.append(item.model_dump())
        elif hasattr(item, "dict"):
            out.append(item.dict())
        else:
            raise ConsentContractError("consents[] enthält ungültige Elemente")
    return out


def _open_db_if_needed(db: Optional[SASession]) -> Tuple[SASession, Optional[Any]]:
    if db is not None:
        return db, None
    gen = get_db()
    db2 = next(gen)
    return db2, gen


def _close_db_gen(gen: Optional[Any]) -> None:
    if gen is None:
        return
    try:
        gen.close()
    except Exception:
        pass


def record_consent(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Unterstützt Call-Patterns:
      - record_consent(user_id, consents)
      - record_consent(db, user_id, consents)
      - record_consent(user_id=<>, consents=<>, db=<>)
    """
    db = kwargs.get("db")
    user_id = kwargs.get("user_id")
    consents = kwargs.get("consents")

    if len(args) == 2 and user_id is None and consents is None:
        user_id, consents = args
    elif len(args) == 3 and db is None and user_id is None and consents is None:
        db, user_id, consents = args

    if db is not None and not isinstance(db, SASession):
        db = None

    if not user_id:
        raise ConsentContractError("user_id fehlt")

    raw = _coerce_consents(consents)
    normalized = validate_and_normalize_consents(raw)
    ensure_required_consents(normalized)

    db2, gen = _open_db_if_needed(db)
    try:
        record_consents(db2, str(user_id), normalized)
        return {"ok": True}
    finally:
        _close_db_gen(gen)


def get_consent_status(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Unterstützt Call-Patterns:
      - get_consent_status(user_id)
      - get_consent_status(db, user_id)
      - get_consent_status(user_id=<>, db=<>)
    """
    db = kwargs.get("db")
    user_id = kwargs.get("user_id")

    if len(args) == 1 and user_id is None:
        user_id = args[0]
    elif len(args) == 2 and user_id is None and db is None:
        db, user_id = args

    if db is not None and not isinstance(db, SASession):
        db = None

    if not user_id:
        raise ConsentContractError("user_id fehlt")

    db2, gen = _open_db_if_needed(db)
    try:
        accepted = get_user_consents(db2, str(user_id))
        required = required_consents()
        have = {(a["doc_type"], a["doc_version"]) for a in accepted}
        is_complete = all((r["doc_type"], r["doc_version"]) in have for r in required)
        return {"required": required, "accepted": accepted, "is_complete": is_complete}
    finally:
        _close_db_gen(gen)