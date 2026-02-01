from app.guards import forbid_moderator
import datetime as dt
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import MetaData, Table, select, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.services.export_store import issue_one_time_token, consume_one_time_token
from app.services.export_redaction import redact_masterclipboard_row
from app.services.export_crypto import encrypt_json
from app.services.export_audit import write_export_audit

# WICHTIG: wir nutzen exakt die gleichen Dependencies wie im funktionierenden Export-Vehicle Router
from app.routers.export_vehicle import get_db, get_actor  # type: ignore


router = APIRouter(prefix="/export/masterclipboard", tags=["export"], dependencies=[Depends(forbid_moderator)])


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


def _masterclipboard_table(db: Session) -> Table:
    # WICHTIG: gleiche Connection nutzen (sqlite :memory: safe)
    conn = db.connection()
    insp = sa_inspect(conn)

    candidates = (
        "masterclipboard",
        "masterclipboards",
        "master_clipboard",
        "master_clipboards",
        "masterclipboard_sessions",
        "masterclipboard_session",
    )

    for name in candidates:
        if insp.has_table(name):
            return Table(name, MetaData(), autoload_with=conn)

    raise HTTPException(status_code=500, detail="masterclipboard_table_missing")


def _fetch_masterclipboard_row(db: Session, masterclipboard_id: str) -> Dict[str, Any]:
    t = _masterclipboard_table(db)
    if "id" not in t.c:
        raise HTTPException(status_code=500, detail="masterclipboard_id_column_missing")

    row = db.execute(
        select(t).where(t.c.id == masterclipboard_id).limit(1)
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="not_found")

    return dict(row)


@router.get("/{masterclipboard_id}")
def export_masterclipboard_redacted(
    masterclipboard_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    # MasterClipboard ist Gewerbe/Dealer: redacted export nur dealer/admin/superadmin
    _require_roles(actor, {"dealer", "admin", "superadmin"})

    mc_row = _fetch_masterclipboard_row(db, masterclipboard_id)
    redacted = redact_masterclipboard_row(mc_row)

    write_export_audit(
        db,
        event_type="EXPORT_MASTERCLIPBOARD_REDACTED",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="masterclipboard",
        target_id=masterclipboard_id,
        success=True,
        reason=None,
    )

    return {"target": "masterclipboard", "id": masterclipboard_id, "data": redacted}


@router.post("/{masterclipboard_id}/grant")
def export_masterclipboard_full_grant(
    masterclipboard_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    # Full-Grant nur SUPERADMIN
    _require_roles(actor, {"superadmin"})

    # existence check (404 wenn nicht da)
    _ = _fetch_masterclipboard_row(db, masterclipboard_id)

    token, expires_at = issue_one_time_token(
        db,
        resource_type="masterclipboard",
        resource_id=masterclipboard_id,
        issued_by_role=_actor_role(actor),
        issued_by_user_id=_actor_user_id(actor),
    )

    write_export_audit(
        db,
        event_type="EXPORT_MASTERCLIPBOARD_GRANT",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="masterclipboard",
        target_id=masterclipboard_id,
        success=True,
        reason=None,
    )

    return {"export_token": token, "expires_at": expires_at.isoformat()}


@router.get("/{masterclipboard_id}/full")
def export_masterclipboard_full_encrypted(
    masterclipboard_id: str,
    x_export_token: Optional[str] = Header(default=None, alias="X-Export-Token"),
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
):
    # Full nur SUPERADMIN
    _require_roles(actor, {"superadmin"})

    if not x_export_token:
        write_export_audit(
            db,
            event_type="EXPORT_MASTERCLIPBOARD_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="masterclipboard",
            target_id=masterclipboard_id,
            success=False,
            reason="missing_x_export_token",
        )
        raise HTTPException(status_code=400, detail="missing_x_export_token")

    try:
        _ = consume_one_time_token(db, "masterclipboard", masterclipboard_id, x_export_token)
    except PermissionError as e:
        write_export_audit(
            db,
            event_type="EXPORT_MASTERCLIPBOARD_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="masterclipboard",
            target_id=masterclipboard_id,
            success=False,
            reason=str(e),
        )
        raise HTTPException(status_code=403, detail="export_token_invalid")

    mc_row = _fetch_masterclipboard_row(db, masterclipboard_id)

    payload = {"target": "masterclipboard", "id": masterclipboard_id, "masterclipboard": mc_row}
    ciphertext = encrypt_json(payload)

    write_export_audit(
        db,
        event_type="EXPORT_MASTERCLIPBOARD_FULL",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="masterclipboard",
        target_id=masterclipboard_id,
        success=True,
        reason=None,
    )

    return {"target": "masterclipboard", "id": masterclipboard_id, "ciphertext": ciphertext}

