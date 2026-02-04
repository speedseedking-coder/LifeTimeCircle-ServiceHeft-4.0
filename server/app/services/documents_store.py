server/app/services/documents_store.py
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> str:
    # Default passend zu deinem Setup: server/data/app.db
    return os.getenv("LTC_DB_PATH", os.path.join(".", "data", "app.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id              TEXT PRIMARY KEY,
            owner_user_id        TEXT NOT NULL,
            original_filename    TEXT NOT NULL,
            stored_name          TEXT NOT NULL,
            content_type         TEXT NOT NULL,
            size_bytes           INTEGER NOT NULL,
            status               TEXT NOT NULL, -- quarantine | approved | rejected
            created_at           TEXT NOT NULL,

            approved_at          TEXT NULL,
            approved_by          TEXT NULL,

            rejected_at          TEXT NULL,
            rejected_by          TEXT NULL,
            rejection_reason     TEXT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_user_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);")


@dataclass(frozen=True)
class Document:
    doc_id: str
    owner_user_id: str
    original_filename: str
    stored_name: str
    content_type: str
    size_bytes: int
    status: str
    created_at: str
    approved_at: Optional[str]
    approved_by: Optional[str]
    rejected_at: Optional[str]
    rejected_by: Optional[str]
    rejection_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "owner_user_id": self.owner_user_id,
            "original_filename": self.original_filename,
            "stored_name": self.stored_name,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "rejected_at": self.rejected_at,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
        }


def create_quarantine_document(
    *,
    owner_user_id: str,
    original_filename: str,
    stored_name: str,
    content_type: str,
    size_bytes: int,
) -> Document:
    doc_id = f"doc_{uuid4().hex}"
    now = _utc_now_iso()

    with _connect() as conn:
        _ensure_tables(conn)
        conn.execute(
            """
            INSERT INTO documents (
                doc_id, owner_user_id, original_filename, stored_name,
                content_type, size_bytes, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (doc_id, owner_user_id, original_filename, stored_name, content_type, size_bytes, "quarantine", now),
        )
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ? LIMIT 1;", (doc_id,)).fetchone()
        assert row is not None
        return _row_to_doc(row)


def get_document(doc_id: str) -> Optional[Document]:
    with _connect() as conn:
        _ensure_tables(conn)
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ? LIMIT 1;", (doc_id,)).fetchone()
        if row is None:
            return None
        return _row_to_doc(row)


def list_quarantine(limit: int = 50) -> list[Document]:
    with _connect() as conn:
        _ensure_tables(conn)
        rows = conn.execute(
            "SELECT * FROM documents WHERE status = 'quarantine' ORDER BY created_at DESC LIMIT ?;",
            (int(limit),),
        ).fetchall()
        return [_row_to_doc(r) for r in rows]


def mark_approved(doc_id: str, *, approved_by: str) -> Optional[Document]:
    now = _utc_now_iso()
    with _connect() as conn:
        _ensure_tables(conn)
        cur = conn.execute(
            """
            UPDATE documents
               SET status = 'approved',
                   approved_at = ?,
                   approved_by = ?,
                   rejected_at = NULL,
                   rejected_by = NULL,
                   rejection_reason = NULL
             WHERE doc_id = ?;
            """,
            (now, approved_by, doc_id),
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ? LIMIT 1;", (doc_id,)).fetchone()
        assert row is not None
        return _row_to_doc(row)


def mark_rejected(doc_id: str, *, rejected_by: str, reason: str) -> Optional[Document]:
    now = _utc_now_iso()
    with _connect() as conn:
        _ensure_tables(conn)
        cur = conn.execute(
            """
            UPDATE documents
               SET status = 'rejected',
                   rejected_at = ?,
                   rejected_by = ?,
                   rejection_reason = ?,
                   approved_at = NULL,
                   approved_by = NULL
             WHERE doc_id = ?;
            """,
            (now, rejected_by, reason, doc_id),
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ? LIMIT 1;", (doc_id,)).fetchone()
        assert row is not None
        return _row_to_doc(row)


def _row_to_doc(row: sqlite3.Row) -> Document:
    d = dict(row)
    return Document(
        doc_id=d["doc_id"],
        owner_user_id=d["owner_user_id"],
        original_filename=d["original_filename"],
        stored_name=d["stored_name"],
        content_type=d["content_type"],
        size_bytes=int(d["size_bytes"]),
        status=d["status"],
        created_at=d["created_at"],
        approved_at=d.get("approved_at"),
        approved_by=d.get("approved_by"),
        rejected_at=d.get("rejected_at"),
        rejected_by=d.get("rejected_by"),
        rejection_reason=d.get("rejection_reason"),
    )
