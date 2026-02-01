# server/app/consent_store.py
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple


_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_consent (
  user_id TEXT NOT NULL,
  consent_version TEXT NOT NULL,
  accepted_at TEXT NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (user_id, consent_version)
);
"""


_ALLOWED_SOURCES = {"web", "app", "api", "unknown"}


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_source(source: Optional[str]) -> str:
    if not source:
        return "unknown"
    s = str(source).strip().lower()
    return s if s in _ALLOWED_SOURCES else "unknown"


def ensure_consent_table(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA foreign_keys=ON;")
        con.executescript(_TABLE_SQL)
        con.commit()


def record_consent(db_path: str, user_id: str, consent_version: str, source: str = "web") -> str:
    """
    Speichert Consent pro (user_id, consent_version).
    - idempotent: erneutes Accept derselben Version überschreibt NICHT den ersten Timestamp
    - auditierbar: Version + accepted_at (UTC) + source
    """
    ensure_consent_table(db_path)

    src = _norm_source(source)
    ts = _utc_iso_now()

    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON;")

        con.execute(
            """
            INSERT OR IGNORE INTO user_consent (user_id, consent_version, accepted_at, source)
            VALUES (?, ?, ?, ?)
            """,
            (str(user_id), str(consent_version), ts, src),
        )

        row = con.execute(
            """
            SELECT accepted_at
            FROM user_consent
            WHERE user_id = ? AND consent_version = ?
            """,
            (str(user_id), str(consent_version)),
        ).fetchone()
        con.commit()

    return str(row["accepted_at"]) if row else ts


def has_consent(db_path: str, user_id: str, consent_version: str) -> bool:
    ensure_consent_table(db_path)
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            """
            SELECT 1
            FROM user_consent
            WHERE user_id = ? AND consent_version = ?
            LIMIT 1
            """,
            (str(user_id), str(consent_version)),
        ).fetchone()
        return row is not None


@dataclass(frozen=True)
class ConsentStatus:
    required_version: str
    has_required: bool
    latest_version: Optional[str]
    latest_accepted_at: Optional[str]
    latest_source: Optional[str]


def get_consent_status(db_path: str, user_id: str, required_version: str) -> ConsentStatus:
    ensure_consent_table(db_path)

    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        latest = con.execute(
            """
            SELECT consent_version, accepted_at, source
            FROM user_consent
            WHERE user_id = ?
            ORDER BY accepted_at DESC
            LIMIT 1
            """,
            (str(user_id),),
        ).fetchone()

    latest_version = str(latest["consent_version"]) if latest else None
    latest_accepted_at = str(latest["accepted_at"]) if latest else None
    latest_source = str(latest["source"]) if latest else None

    return ConsentStatus(
        required_version=str(required_version),
        has_required=has_consent(db_path, str(user_id), str(required_version)),
        latest_version=latest_version,
        latest_accepted_at=latest_accepted_at,
        latest_source=latest_source,
    )


def env_db_path(default: str = "./data/app.db") -> str:
    return os.getenv("LTC_DB_PATH", default)


def env_consent_version(default: str = "2026-01-27") -> str:
    return os.getenv("LTC_CONSENT_VERSION", default)
