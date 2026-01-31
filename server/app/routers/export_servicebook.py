import datetime as dt
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import MetaData, Table, select, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.services.export_store import issue_one_time_token, consume_one_time_token
from app.services.export_crypto import encrypt_json
from app.services.export_audit import write_export_audit
from app.services.export_servicebook_redaction import redact_servicebook_entry_row

# Wichtig: exakt die gleichen Dependencies wie im funktionierenden Export-Vehicle Router
from app.routers.export_vehicle import get_db, get_actor  # type: ignore


router = APIRouter(prefix="/export/servicebook", tags=["export"])


# ---------------------------
# actor helpers
# ---------------------------
def _actor_role(actor: Any) -> str:
    if actor is None:
        return "public"
    r = getattr(actor, "role", None)
    if isinstance(r, str) and r:
        return r
    if isinstance(actor, dict):
        rr = actor.get("role")
        if isinstance(rr, str) and rr:
            return rr
    return "public"


def _actor_user_id(actor: Any) -> Optional[str]:
    if actor is None:
        return None
    u = getattr(actor, "user_id", None)
    if isinstance(u, str) and u:
        return u
    if isinstance(actor, dict):
        uu = actor.get("user_id")
        if isinstance(uu, str) and uu:
            return uu
    return None


def _require_roles(actor: Any, allowed: set[str]) -> None:
    role = _actor_role(actor)
    if role not in allowed:
        raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------
# DB helpers (autodetect)
# ---------------------------
def _servicebook_entries_table(db: Session) -> Table:
    """
    Servicebook ist im Core noch nicht als SQLAlchemy-Model vorhanden.
    Daher: Table autodetect (wie export_vehicle).
    """
    conn = db.connection()
    insp = sa_inspect(conn)

    candidates = (
        "servicebook_entries",
        "servicebook_entry",
        "service_entries",
        "service_entry",
        "servicebook",
        "servicebooks",
    )

    for name in candidates:
        if insp.has_table(name):
            return Table(name, MetaData(), autoload_with=conn)

    raise HTTPException(status_code=404, detail="servicebook_table_missing")


def _fetch_servicebook_entries(db: Session, servicebook_id: str) -> List[Dict[str, Any]]:
    t = _servicebook_entries_table(db)

    # Wir akzeptieren diese Key-Varianten:
    # - servicebook_id (bevorzugt)
    # - vehicle_id (falls Servicebook == Vehicle-Buch)
    # - id (falls Servicebook als Record statt Entries geführt wird)
    if "servicebook_id" in t.c:
        where_col = t.c.servicebook_id
    elif "vehicle_id" in t.c:
        where_col = t.c.vehicle_id
    elif "id" in t.c:
        where_col = t.c.id
    else:
        raise HTTPException(status_code=500, detail="servicebook_id_column_missing")

    rows = db.execute(
        select(t).where(where_col == servicebook_id)
    ).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="not_found")

    return [dict(r) for r in rows]


def _enforce_scope_or_admin(actor: Any, rows: List[Dict[str, Any]]) -> None:
    """
    Rollen:
    - user/vip/dealer: nur eigener Scope (Owner)
    - admin/superadmin: ok
    - moderator/public: nie
    """
    role = _actor_role(actor)

    if role in {"admin", "superadmin"}:
        return

    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    actor_uid = _actor_user_id(actor)
    if not actor_uid:
        raise HTTPException(status_code=403, detail="forbidden")

    # Owner-Spalte finden (best effort)
    owner_keys = (
        "owner_id",
        "user_id",
        "created_by_user_id",
        "created_by",
        "actor_user_id",
    )

    for row in rows:
        for k in owner_keys:
            if k in row and row[k]:
                if str(row[k]) == str(actor_uid):
                    return

    # Kein Owner-Match => forbidden
    raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------
# Endpoints
# ---------------------------
@router.get("/{servicebook_id}")
def export_servicebook_redacted(
    servicebook_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    rows = _fetch_servicebook_entries(db, servicebook_id)
    _enforce_scope_or_admin(actor, rows)

    redacted = [redact_servicebook_entry_row(r) for r in rows]

    write_export_audit(
        db,
        event_type="EXPORT_SERVICEBOOK_REDACTED",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="servicebook",
        target_id=servicebook_id,
        success=True,
        reason=None,
    )

    return {"target": "servicebook", "id": servicebook_id, "entries": redacted}


@router.post("/{servicebook_id}/grant")
def export_servicebook_full_grant(
    servicebook_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    _require_roles(actor, {"superadmin"})

    # existence check
    _ = _fetch_servicebook_entries(db, servicebook_id)

    token, expires_at = issue_one_time_token(
        db,
        resource_type="servicebook",
        resource_id=servicebook_id,
        issued_by_role=_actor_role(actor),
        issued_by_user_id=_actor_user_id(actor),
    )

    write_export_audit(
        db,
        event_type="EXPORT_SERVICEBOOK_GRANT",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="servicebook",
        target_id=servicebook_id,
        success=True,
        reason=None,
    )

    return {"export_token": token, "expires_at": expires_at.isoformat()}


@router.get("/{servicebook_id}/full")
def export_servicebook_full_encrypted(
    servicebook_id: str,
    x_export_token: Optional[str] = Header(default=None, alias="X-Export-Token"),
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    _require_roles(actor, {"superadmin"})

    if not x_export_token:
        write_export_audit(
            db,
            event_type="EXPORT_SERVICEBOOK_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="servicebook",
            target_id=servicebook_id,
            success=False,
            reason="missing_x_export_token",
        )
        raise HTTPException(status_code=400, detail="missing_x_export_token")

    try:
        _ = consume_one_time_token(db, "servicebook", servicebook_id, x_export_token)
    except PermissionError as e:
        write_export_audit(
            db,
            event_type="EXPORT_SERVICEBOOK_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="servicebook",
            target_id=servicebook_id,
            success=False,
            reason=str(e),
        )
        raise HTTPException(status_code=403, detail="export_token_invalid")

    rows = _fetch_servicebook_entries(db, servicebook_id)

    payload = {
        "target": "servicebook",
        "id": servicebook_id,
        "exported_at": dt.datetime.now(dt.timezone.utc),
        "entries": rows,
    }
    ciphertext = encrypt_json(payload)

    write_export_audit(
        db,
        event_type="EXPORT_SERVICEBOOK_FULL",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="servicebook",
        target_id=servicebook_id,
        success=True,
        reason=None,
    )

    return {"target": "servicebook", "id": servicebook_id, "ciphertext": ciphertext}
