from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Tuple

_DB_LOCK = threading.Lock()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db(db_path: str) -> Iterator[sqlite3.Connection]:
    # WAL + lock für simple konsistente Writes
    with _DB_LOCK:
        conn = _connect(db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db(db_path: str) -> None:
    with db(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id TEXT PRIMARY KEY,
                email_hmac TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_challenges (
                challenge_id TEXT PRIMARY KEY,
                email_hmac TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_challenges_email ON auth_challenges(email_hmac);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                doc_version TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                source TEXT NOT NULL,
                ip_hmac TEXT NULL,
                ua_hmac TEXT NULL,
                evidence_hash TEXT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_consents_user ON auth_consents(user_id);")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_rate_limits (
                key TEXT PRIMARY KEY,
                window_start TEXT NOT NULL,
                count INTEGER NOT NULL
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_audit (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NULL,
                scope TEXT NOT NULL,
                result TEXT NOT NULL,
                request_id TEXT NOT NULL,
                correlation_id TEXT NULL,
                reason_code TEXT NULL,
                redacted_metadata TEXT NULL
            );
            """
        )


def upsert_user(conn: sqlite3.Connection, user_id: str, email_hmac: str, created_at: str) -> None:
    conn.execute(
        """
        INSERT INTO auth_users(user_id, email_hmac, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(email_hmac) DO NOTHING;
        """,
        (user_id, email_hmac, created_at),
    )


def get_user_by_email_hmac(conn: sqlite3.Connection, email_hmac: str) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM auth_users WHERE email_hmac = ? LIMIT 1;", (email_hmac,))
    return cur.fetchone()


def insert_challenge(
    conn: sqlite3.Connection,
    challenge_id: str,
    email_hmac: str,
    otp_hash: str,
    created_at: str,
    expires_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO auth_challenges(challenge_id, email_hmac, otp_hash, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        (challenge_id, email_hmac, otp_hash, created_at, expires_at),
    )


def get_challenge(conn: sqlite3.Connection, challenge_id: str) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM auth_challenges WHERE challenge_id = ? LIMIT 1;", (challenge_id,))
    return cur.fetchone()


def mark_challenge_attempt(conn: sqlite3.Connection, challenge_id: str, attempts: int, last_attempt_at: str) -> None:
    conn.execute(
        """
        UPDATE auth_challenges
        SET attempts = ?, last_attempt_at = ?
        WHERE challenge_id = ?;
        """,
        (attempts, last_attempt_at, challenge_id),
    )


def mark_challenge_used(conn: sqlite3.Connection, challenge_id: str, used_at: str) -> None:
    conn.execute(
        """
        UPDATE auth_challenges
        SET used_at = ?
        WHERE challenge_id = ?;
        """,
        (used_at, challenge_id),
    )


def insert_session(
    conn: sqlite3.Connection,
    session_id: str,
    user_id: str,
    token_hash: str,
    created_at: str,
    expires_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO auth_sessions(session_id, user_id, token_hash, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        (session_id, user_id, token_hash, created_at, expires_at),
    )


def get_session_by_token_hash(conn: sqlite3.Connection, token_hash: str) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT * FROM auth_sessions
        WHERE token_hash = ? AND revoked_at IS NULL
        LIMIT 1;
        """,
        (token_hash,),
    )
    return cur.fetchone()


def revoke_session(conn: sqlite3.Connection, token_hash: str, revoked_at: str) -> None:
    conn.execute("UPDATE auth_sessions SET revoked_at = ? WHERE token_hash = ?;", (revoked_at, token_hash))


def insert_consent(
    conn: sqlite3.Connection,
    user_id: str,
    doc_type: str,
    doc_version: str,
    accepted_at: str,
    source: str,
    ip_hmac: Optional[str],
    ua_hmac: Optional[str],
    evidence_hash: Optional[str],
) -> None:
    conn.execute(
        """
        INSERT INTO auth_consents(user_id, doc_type, doc_version, accepted_at, source, ip_hmac, ua_hmac, evidence_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (user_id, doc_type, doc_version, accepted_at, source, ip_hmac, ua_hmac, evidence_hash),
    )


def list_consents(conn: sqlite3.Connection, user_id: str) -> list[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM auth_consents WHERE user_id = ?;", (user_id,))
    return cur.fetchall()


def rate_limit_get(conn: sqlite3.Connection, key: str) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM auth_rate_limits WHERE key = ? LIMIT 1;", (key,))
    return cur.fetchone()


def rate_limit_set(conn: sqlite3.Connection, key: str, window_start: str, count: int) -> None:
    conn.execute(
        """
        INSERT INTO auth_rate_limits(key, window_start, count)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET window_start=excluded.window_start, count=excluded.count;
        """,
        (key, window_start, count),
    )


def audit_insert(
    conn: sqlite3.Connection,
    event_id: str,
    created_at: str,
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[str],
    scope: str,
    result: str,
    request_id: str,
    correlation_id: Optional[str],
    reason_code: Optional[str],
    redacted_metadata: Optional[Dict[str, Any]],
) -> None:
    meta_json = json.dumps(redacted_metadata, ensure_ascii=False) if redacted_metadata else None
    conn.execute(
        """
        INSERT INTO auth_audit(
            event_id, created_at, actor_id, actor_role, action, target_type, target_id, scope, result,
            request_id, correlation_id, reason_code, redacted_metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            event_id,
            created_at,
            actor_id,
            actor_role,
            action,
            target_type,
            target_id,
            scope,
            result,
            request_id,
            correlation_id,
            reason_code,
            meta_json,
        ),
    )
