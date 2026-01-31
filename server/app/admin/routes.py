from __future__ import annotations

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.rbac import AuthContext, require_roles
from app.auth.settings import load_settings


router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_ROLES = {"public", "user", "vip", "dealer", "moderator", "admin"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1;",
        (name,),
    ).fetchone()
    return row is not None


def _ensure_auth_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_audit_events (
            event_id TEXT PRIMARY KEY,
            at TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            target_user_id TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_audit_at ON auth_audit_events(at);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_audit_target ON auth_audit_events(target_user_id);"
    )


def _best_effort_insert_into_audit_events(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    """
    Best effort: wenn es bereits eine audit_events Tabelle gibt (z.B. aus dem Hauptsystem),
    versuchen wir kompatibel zu schreiben, ohne Schema-Annahmen zu erzwingen.
    """
    if not _table_exists(conn, "audit_events"):
        return

    cols = [r["name"] for r in conn.execute("PRAGMA table_info(audit_events);").fetchall()]
    if not cols:
        return

    values: Dict[str, Any] = {}

    # IDs
    if "event_id" in cols:
        values["event_id"] = payload["event_id"]
    elif "id" in cols:
        values["id"] = payload["event_id"]

    # Zeit
    if "at" in cols:
        values["at"] = payload["at"]
    elif "created_at" in cols:
        values["created_at"] = payload["at"]
    elif "ts" in cols:
        values["ts"] = payload["at"]

    # Typ/Aktion
    if "action" in cols:
        values["action"] = payload["action"]
    elif "event_type" in cols:
        values["event_type"] = payload["action"]
    elif "type" in cols:
        values["type"] = payload["action"]

    # Result
    if "result" in cols:
        values["result"] = payload["result"]
    elif "status" in cols:
        values["status"] = payload["result"]

    # Actor/Target
    if "actor_user_id" in cols:
        values["actor_user_id"] = payload["actor_user_id"]
    elif "actor_id" in cols:
        values["actor_id"] = payload["actor_user_id"]

    if "target_user_id" in cols:
        values["target_user_id"] = payload["target_user_id"]
    elif "target_id" in cols:
        values["target_id"] = payload["target_user_id"]

    # Meta
    meta_json = payload.get("details_json", "{}")
    if "details_json" in cols:
        values["details_json"] = meta_json
    elif "meta_json" in cols:
        values["meta_json"] = meta_json
    elif "meta" in cols:
        values["meta"] = meta_json

    # Wenn praktisch nichts gemappt werden konnte: abbrechen
    if len(values) < 3:
        return

    col_list = ", ".join(values.keys())
    placeholders = ", ".join(["?"] * len(values))
    conn.execute(
        f"INSERT INTO audit_events ({col_list}) VALUES ({placeholders});",
        tuple(values.values()),
    )


class RoleSetRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=32)
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class ModeratorAccreditRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class RoleSetResponse(BaseModel):
    ok: bool
    user_id: str
    old_role: str
    new_role: str
    at: str


class AdminUserRow(BaseModel):
    user_id: str
    role: str
    created_at: str


def _apply_role_change(
    *,
    conn: sqlite3.Connection,
    user_id: str,
    new_role: str,
    actor: AuthContext,
    action: str,
    reason_provided: bool,
) -> RoleSetResponse:
    now_iso = _utc_now_iso()

    if not _table_exists(conn, "auth_users"):
        raise HTTPException(status_code=404, detail="user_not_found")

    row = conn.execute(
        "SELECT role FROM auth_users WHERE user_id=? LIMIT 1;",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="user_not_found")

    old_role = (row["role"] or "").strip().lower()

    # no-op ist erlaubt, aber wir auditieren trotzdem
    conn.execute(
        "UPDATE auth_users SET role=? WHERE user_id=?;",
        (new_role, user_id),
    )

    # Audit (minimal + ohne PII / kein Freitext)
    _ensure_auth_audit_table(conn)
    event_id = str(uuid.uuid4())
    details = {
        "old_role": old_role,
        "new_role": new_role,
        "reason_provided": bool(reason_provided),
    }
    payload = {
        "event_id": event_id,
        "at": now_iso,
        "action": action,
        "result": "success",
        "actor_user_id": actor.user_id,
        "target_user_id": user_id,
        "details_json": json.dumps(details, ensure_ascii=False, separators=(",", ":")),
    }

    conn.execute(
        """
        INSERT INTO auth_audit_events(event_id, at, action, result, actor_user_id, target_user_id, details_json)
        VALUES(?, ?, ?, ?, ?, ?, ?);
        """,
        (
            payload["event_id"],
            payload["at"],
            payload["action"],
            payload["result"],
            payload["actor_user_id"],
            payload["target_user_id"],
            payload["details_json"],
        ),
    )

    # Optional: best-effort in bestehendes audit_events Schema, falls vorhanden
    try:
        _best_effort_insert_into_audit_events(conn, payload)
    except Exception:
        # Audit darf Admin-Action nicht killen, aber auth_audit_events ist bereits geschrieben.
        pass

    return RoleSetResponse(
        ok=True,
        user_id=user_id,
        old_role=old_role,
        new_role=new_role,
        at=now_iso,
    )


@router.get("/users", response_model=List[AdminUserRow])
def admin_list_users(_: AuthContext = Depends(require_roles("admin", "superadmin"))):
    """
    Minimaler Admin-Überblick: keine Klartext-PII, nur user_id/role/created_at.
    """
    settings = load_settings()
    with _connect(settings.db_path) as conn:
        if not _table_exists(conn, "auth_users"):
            return []
        rows = conn.execute(
            "SELECT user_id, role, created_at FROM auth_users ORDER BY created_at DESC LIMIT 200;"
        ).fetchall()
        return [AdminUserRow(user_id=r["user_id"], role=r["role"], created_at=r["created_at"]) for r in rows]


@router.post("/users/{user_id}/role", response_model=RoleSetResponse)
def admin_set_user_role(
    user_id: str,
    body: RoleSetRequest,
    actor: AuthContext = Depends(require_roles("admin", "superadmin")),
):
    new_role = (body.role or "").strip().lower()
    if new_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_role",
        )

    settings = load_settings()
    with _connect(settings.db_path) as conn:
        return _apply_role_change(
            conn=conn,
            user_id=user_id,
            new_role=new_role,
            actor=actor,
            action="ADMIN_ROLE_SET",
            reason_provided=bool(body.reason),
        )


@router.post("/users/{user_id}/moderator", response_model=RoleSetResponse)
def admin_accredit_moderator(
    user_id: str,
    body: ModeratorAccreditRequest,
    actor: AuthContext = Depends(require_roles("admin", "superadmin")),
):
    """
    Komfort-Endpoint: Moderator akkreditieren (setzt Rolle auf 'moderator').

    - serverseitig RBAC: nur admin
    - Audit ohne Freitext/PII (reason_provided bool)
    """
    settings = load_settings()
    with _connect(settings.db_path) as conn:
        return _apply_role_change(
            conn=conn,
            user_id=user_id,
            new_role="moderator",
            actor=actor,
            action="ADMIN_MODERATOR_ACCREDIT",
            reason_provided=bool(body.reason),
        )
