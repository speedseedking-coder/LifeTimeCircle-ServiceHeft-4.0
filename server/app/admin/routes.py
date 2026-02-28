from __future__ import annotations

from app.guards import forbid_moderator

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.rbac import AuthContext, require_roles
from app.auth.settings import load_settings


router = APIRouter(dependencies=[Depends(forbid_moderator)], prefix="/admin", tags=["admin"])

# Wichtig: SUPERADMIN existiert als Rolle (für High-Risk-Gates)
ALLOWED_ROLES = {"public", "user", "vip", "dealer", "moderator", "admin", "superadmin"}


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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_audit_at ON auth_audit_events(at);")
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


def _audit(
    conn: sqlite3.Connection,
    *,
    action: str,
    actor_user_id: str,
    target_user_id: str,
    details: Dict[str, Any],
) -> None:
    """
    Audit ohne Klartext-PII. Keine Secrets.
    """
    _ensure_auth_audit_table(conn)
    payload = {
        "event_id": str(uuid.uuid4()),
        "at": _utc_now_iso(),
        "action": action,
        "result": "success",
        "actor_user_id": actor_user_id,
        "target_user_id": target_user_id,
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

    try:
        _best_effort_insert_into_audit_events(conn, payload)
    except Exception:
        # Audit darf Admin-Action nicht killen
        pass


def _ensure_vip_business_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vip_businesses (
            business_id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            approved_at TEXT,
            approved_by_user_id TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vip_business_staff (
            business_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (business_id, user_id),
            FOREIGN KEY (business_id) REFERENCES vip_businesses(business_id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_business_owner ON vip_businesses(owner_user_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_staff_business ON vip_business_staff(business_id);")


class RoleSetRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=32)
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class ModeratorAccreditRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class VipBusinessCreateRequest(BaseModel):
    owner_user_id: str = Field(..., min_length=8, max_length=64)
    # optional, falls du eine externe Business-ID hast
    business_id: Optional[str] = Field(default=None, min_length=8, max_length=64)
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class VipBusinessResponse(BaseModel):
    ok: bool
    business_id: str
    owner_user_id: str
    approved: bool
    created_at: str
    approved_at: Optional[str] = None
    approved_by_user_id: Optional[str] = None


class VipBusinessStaffAddRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=200)  # wird NICHT als Text auditiert


class VipBusinessStaffAddResponse(BaseModel):
    ok: bool
    business_id: str
    user_id: str
    at: str


class VipBusinessListRow(BaseModel):
    business_id: str
    owner_user_id: str
    approved: bool
    created_at: str
    approved_at: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    staff_user_ids: List[str] = Field(default_factory=list)
    staff_count: int = 0


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


def _vip_business_row_to_response(row: sqlite3.Row) -> VipBusinessResponse:
    return VipBusinessResponse(
        ok=True,
        business_id=row["business_id"],
        owner_user_id=row["owner_user_id"],
        approved=bool(row["approved_at"]),
        created_at=row["created_at"],
        approved_at=row["approved_at"],
        approved_by_user_id=row["approved_by_user_id"],
    )


def _list_vip_businesses(conn: sqlite3.Connection) -> List[VipBusinessListRow]:
    if not _table_exists(conn, "vip_businesses"):
        return []

    rows = conn.execute(
        """
        SELECT business_id, owner_user_id, created_at, approved_at, approved_by_user_id
        FROM vip_businesses
        ORDER BY created_at DESC, business_id DESC;
        """
    ).fetchall()
    if not rows:
        return []

    staff_rows = conn.execute(
        """
        SELECT business_id, user_id
        FROM vip_business_staff
        ORDER BY created_at ASC, user_id ASC;
        """
    ).fetchall() if _table_exists(conn, "vip_business_staff") else []

    staff_by_business: Dict[str, List[str]] = {}
    for staff_row in staff_rows:
        business_id = str(staff_row["business_id"])
        staff_by_business.setdefault(business_id, []).append(str(staff_row["user_id"]))

    return [
        VipBusinessListRow(
            business_id=row["business_id"],
            owner_user_id=row["owner_user_id"],
            approved=bool(row["approved_at"]),
            created_at=row["created_at"],
            approved_at=row["approved_at"],
            approved_by_user_id=row["approved_by_user_id"],
            staff_user_ids=staff_by_business.get(str(row["business_id"]), []),
            staff_count=len(staff_by_business.get(str(row["business_id"]), [])),
        )
        for row in rows
    ]


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

    _audit(
        conn,
        action=action,
        actor_user_id=actor.user_id,
        target_user_id=user_id,
        details={
            "old_role": old_role,
            "new_role": new_role,
            "reason_provided": bool(reason_provided),
        },
    )

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


@router.get("/vip-businesses", response_model=List[VipBusinessListRow])
def admin_list_vip_businesses(_: AuthContext = Depends(require_roles("admin", "superadmin"))):
    settings = load_settings()
    with _connect(settings.db_path) as conn:
        _ensure_vip_business_tables(conn)
        return _list_vip_businesses(conn)


@router.post("/users/{user_id}/role", response_model=RoleSetResponse)
def admin_set_user_role(
    user_id: str,
    body: RoleSetRequest,
    actor: AuthContext = Depends(require_roles("admin", "superadmin")),
):
    new_role = (body.role or "").strip().lower()
    if new_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_role")

    # SUPERADMIN darf nur von SUPERADMIN vergeben werden
    if new_role == "superadmin" and actor.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="superadmin_required")

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

    - serverseitig RBAC: admin/superadmin
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


@router.post("/vip-businesses", response_model=VipBusinessResponse)
def admin_create_vip_business(
    body: VipBusinessCreateRequest,
    actor: AuthContext = Depends(require_roles("admin", "superadmin")),
):
    """
    VIP-Gewerbe anlegen (Request). Freigabe (approve) nur SUPERADMIN.
    """
    settings = load_settings()
    now = _utc_now_iso()
    business_id = (body.business_id or str(uuid.uuid4())).strip()

    with _connect(settings.db_path) as conn:
        _ensure_vip_business_tables(conn)

        # Insert (idempotent-ish): wenn exists, liefere bestehenden Zustand zurück
        existing = conn.execute(
            "SELECT business_id, owner_user_id, created_at, approved_at, approved_by_user_id FROM vip_businesses WHERE business_id=? LIMIT 1;",
            (business_id,),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO vip_businesses(business_id, owner_user_id, created_at, approved_at, approved_by_user_id)
                VALUES(?, ?, ?, NULL, NULL);
                """,
                (business_id, body.owner_user_id, now),
            )
            _audit(
                conn,
                action="VIP_BUSINESS_CREATED",
                actor_user_id=actor.user_id,
                target_user_id=body.owner_user_id,
                details={
                    "business_id": business_id,
                    "owner_user_id": body.owner_user_id,
                    "reason_provided": bool(body.reason),
                },
            )
            approved_at = None
            approved_by = None
            created_at = now
            owner_user_id = body.owner_user_id
        else:
            owner_user_id = existing["owner_user_id"]
            created_at = existing["created_at"]
            approved_at = existing["approved_at"]
            approved_by = existing["approved_by_user_id"]

        return VipBusinessResponse(
            ok=True,
            business_id=business_id,
            owner_user_id=owner_user_id,
            approved=bool(approved_at),
            created_at=created_at,
            approved_at=approved_at,
            approved_by_user_id=approved_by,
        )


@router.post("/vip-businesses/{business_id}/approve", response_model=VipBusinessResponse)
def superadmin_approve_vip_business(
    business_id: str,
    actor: AuthContext = Depends(require_roles("superadmin")),
):
    """
    Freigabe nur SUPERADMIN.
    """
    settings = load_settings()
    now = _utc_now_iso()

    with _connect(settings.db_path) as conn:
        _ensure_vip_business_tables(conn)

        row = conn.execute(
            "SELECT business_id, owner_user_id, created_at, approved_at, approved_by_user_id FROM vip_businesses WHERE business_id=? LIMIT 1;",
            (business_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="business_not_found")

        # Set approve (idempotent)
        conn.execute(
            """
            UPDATE vip_businesses
            SET approved_at=COALESCE(approved_at, ?),
                approved_by_user_id=COALESCE(approved_by_user_id, ?)
            WHERE business_id=?;
            """,
            (now, actor.user_id, business_id),
        )

        # Audit (minimal)
        _audit(
            conn,
            action="VIP_BUSINESS_APPROVED",
            actor_user_id=actor.user_id,
            target_user_id=row["owner_user_id"],
            details={"business_id": business_id},
        )

        row2 = conn.execute(
            "SELECT business_id, owner_user_id, created_at, approved_at, approved_by_user_id FROM vip_businesses WHERE business_id=? LIMIT 1;",
            (business_id,),
        ).fetchone()

        return _vip_business_row_to_response(row2)


@router.post("/vip-businesses/{business_id}/staff/{user_id}", response_model=VipBusinessStaffAddResponse)
def superadmin_add_vip_business_staff(
    business_id: str,
    user_id: str,
    body: VipBusinessStaffAddRequest,
    actor: AuthContext = Depends(require_roles("superadmin")),
):
    """
    VIP-Gewerbe Staff hinzufügen:
    - nur SUPERADMIN
    - nur wenn Business freigegeben
    - max. 2 Staff (hart enforced)
    """
    settings = load_settings()
    now = _utc_now_iso()

    with _connect(settings.db_path) as conn:
        _ensure_vip_business_tables(conn)

        biz = conn.execute(
            "SELECT business_id, owner_user_id, approved_at FROM vip_businesses WHERE business_id=? LIMIT 1;",
            (business_id,),
        ).fetchone()
        if biz is None:
            raise HTTPException(status_code=404, detail="business_not_found")
        if not biz["approved_at"]:
            raise HTTPException(status_code=400, detail="business_not_approved")

        # bereits Staff? -> idempotent OK
        existing = conn.execute(
            "SELECT 1 FROM vip_business_staff WHERE business_id=? AND user_id=? LIMIT 1;",
            (business_id, user_id),
        ).fetchone()
        if existing is not None:
            _audit(
                conn,
                action="VIP_BUSINESS_STAFF_ADD_NOOP",
                actor_user_id=actor.user_id,
                target_user_id=user_id,
                details={"business_id": business_id, "reason_provided": bool(body.reason)},
            )
            return VipBusinessStaffAddResponse(ok=True, business_id=business_id, user_id=user_id, at=now)

        # Limit prüfen (max 2 Staff)
        cnt = conn.execute(
            "SELECT COUNT(1) AS c FROM vip_business_staff WHERE business_id=?;",
            (business_id,),
        ).fetchone()["c"]
        if int(cnt) >= 2:
            # keine Zahlen in Fehltexten nötig
            raise HTTPException(status_code=409, detail="staff_limit_reached")

        conn.execute(
            "INSERT INTO vip_business_staff(business_id, user_id, created_at) VALUES(?, ?, ?);",
            (business_id, user_id, now),
        )

        _audit(
            conn,
            action="VIP_BUSINESS_STAFF_ADDED",
            actor_user_id=actor.user_id,
            target_user_id=user_id,
            details={"business_id": business_id, "reason_provided": bool(body.reason)},
        )

        return VipBusinessStaffAddResponse(ok=True, business_id=business_id, user_id=user_id, at=now)
