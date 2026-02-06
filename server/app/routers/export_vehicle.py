from __future__ import annotations
from app.guards import forbid_moderator

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect

from app.services.export_store import issue_one_time_token, consume_one_time_token
from app.services.export_redaction import redact_vehicle_row
from app.services.export_crypto import encrypt_json
from app.services.export_audit import write_export_audit


router = APIRouter(prefix="/export/vehicle", tags=["export"], dependencies=[Depends(forbid_moderator)])


# --- Dependencies (bestehende App-Deps nutzen, falls vorhanden) ---
try:
    from app.deps import get_db as get_db  # type: ignore
except Exception:  # pragma: no cover
    def get_db():  # type: ignore
        raise RuntimeError("app.deps.get_db fehlt")

try:
    from app.deps import get_actor as get_actor  # type: ignore
except Exception:  # pragma: no cover
    def get_actor():  # type: ignore
        raise RuntimeError("app.deps.get_actor fehlt")


def _actor_role(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return str(getattr(actor, "role", "") or "")


def _actor_user_id(actor: Any) -> Optional[str]:
    if actor is None:
        return None
    if isinstance(actor, dict):
        return str(actor.get("user_id") or actor.get("id") or "") or None
    return str(getattr(actor, "user_id", None) or getattr(actor, "id", None) or "") or None


def _require_roles(actor: Any, allowed: set[str]) -> None:
    role = _actor_role(actor)
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


def _vehicle_table(db: Session) -> Table:
    # WICHTIG: gleiche Connection nutzen (sqlite :memory: safe)
    conn = db.connection()
    insp = sa_inspect(conn)
    md = MetaData()

    for name in ("vehicles", "vehicle"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=conn)

    raise HTTPException(status_code=404, detail="vehicle_table_missing")


def _fetch_vehicle_row(db: Session, vehicle_id: str) -> Dict[str, Any]:
    t = _vehicle_table(db)

    if "id" not in t.c:
        raise HTTPException(status_code=500, detail="vehicle_id_column_missing")

    row = db.execute(
        select(t).where(t.c.id == vehicle_id).limit(1)
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="not_found")

    return dict(row)


def _enforce_scope_or_admin(actor: Any, vehicle_row: Dict[str, Any]) -> None:
    role = _actor_role(actor)
    if role in {"admin", "superadmin"}:
        return

    actor_uid = _actor_user_id(actor)
    if not actor_uid:
        raise HTTPException(status_code=403, detail="forbidden")

    # Owner-Felder (best effort) – wenn unklar: deny-by-default
    for key in ("owner_id", "user_id", "account_id", "created_by"):
        if key in vehicle_row and vehicle_row[key]:
            if str(vehicle_row[key]) == str(actor_uid):
                return
            raise HTTPException(status_code=403, detail="forbidden")

    raise HTTPException(status_code=403, detail="forbidden")


@router.get("/{vehicle_id}")
def export_vehicle_redacted(
    vehicle_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
) -> Dict[str, Any]:
    _require_roles(actor, {"user", "vip", "dealer", "admin", "superadmin"})
    vehicle_row = _fetch_vehicle_row(db, vehicle_id)
    _enforce_scope_or_admin(actor, vehicle_row)

    redacted = redact_vehicle_row(vehicle_row)

    write_export_audit(
        db,
        event_type="EXPORT_VEHICLE_REDACTED",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="vehicle",
        target_id=vehicle_id,
        success=True,
        meta={"mode": "redacted"},
    )

    return {"target": "vehicle", "id": vehicle_id, "data": redacted}


@router.post("/{vehicle_id}/grant")
def export_vehicle_full_grant(
    vehicle_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
) -> Dict[str, Any]:
    _require_roles(actor, {"superadmin"})

    _ = _fetch_vehicle_row(db, vehicle_id)

    token, expires_at = issue_one_time_token(
        db,
        resource_type="vehicle",
        resource_id=vehicle_id,
        issued_by_role=_actor_role(actor),
        issued_by_user_id=_actor_user_id(actor),
        ttl_seconds=None,
        uses=1,
    )

    write_export_audit(
        db,
        event_type="EXPORT_VEHICLE_GRANT",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="vehicle",
        target_id=vehicle_id,
        success=True,
        meta={"ttl": "configured", "uses": 1},
    )

    return {"export_token": token, "expires_at": expires_at.isoformat()}


@router.get("/{vehicle_id}/full")
def export_vehicle_full_encrypted(
    vehicle_id: str,
    x_export_token: Optional[str] = Header(default=None, alias="X-Export-Token"),
    db: Session = Depends(get_db),
    actor: Any = Depends(get_actor),
) -> Dict[str, Any]:
    _require_roles(actor, {"superadmin"})
    if not x_export_token:
        write_export_audit(
            db,
            event_type="EXPORT_VEHICLE_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="vehicle",
            target_id=vehicle_id,
            success=False,
            reason="missing_token",
            meta={"mode": "full"},
        )
        raise HTTPException(status_code=400, detail="missing_x_export_token")

    try:
        _grant = consume_one_time_token(db, "vehicle", vehicle_id, x_export_token)
    except PermissionError as e:
        code = str(e)
        write_export_audit(
            db,
            event_type="EXPORT_VEHICLE_FULL",
            actor_role=_actor_role(actor),
            actor_user_id=_actor_user_id(actor),
            target_type="vehicle",
            target_id=vehicle_id,
            success=False,
            reason=code,
            meta={"mode": "full"},
        )
        raise HTTPException(status_code=403, detail="forbidden")

    vehicle_row = _fetch_vehicle_row(db, vehicle_id)

    payload = {"target": "vehicle", "id": vehicle_id, "vehicle": vehicle_row}
    ciphertext = encrypt_json(payload)

    write_export_audit(
        db,
        event_type="EXPORT_VEHICLE_FULL",
        actor_role=_actor_role(actor),
        actor_user_id=_actor_user_id(actor),
        target_type="vehicle",
        target_id=vehicle_id,
        success=True,
        meta={"mode": "full", "grant_id": _grant.get("id")},
    )

    return {"ciphertext": ciphertext}

