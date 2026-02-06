# server/app/routers/export_servicebook.py
from __future__ import annotations

from app.guards import forbid_moderator
import datetime as dt
import json
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import MetaData, Table, select, inspect as sa_inspect
from sqlalchemy.orm import Session

from app.services.export_store import issue_one_time_token, consume_one_time_token
from app.services.export_crypto import encrypt_json
from app.services.export_audit import write_export_audit
from app.services.export_servicebook_redaction import redact_servicebook_entry_row

# Wichtig: exakt die gleichen Dependencies wie im funktionierenden Export-Vehicle Router
from app.routers.export_vehicle import get_db, get_actor  # type: ignore


router = APIRouter(prefix="/export/servicebook", tags=["export"], dependencies=[Depends(forbid_moderator)])


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


def _documents_table(db: Session) -> Optional[Table]:
    conn = db.connection()
    insp = sa_inspect(conn)

    candidates = (
        "documents",
        "document",
        "uploads",
        "upload",
        "document_uploads",
        "upload_documents",
    )
    for name in candidates:
        if insp.has_table(name):
            return Table(name, MetaData(), autoload_with=conn)
    return None


def _pick_col(t: Table, names: tuple[str, ...]) -> Optional[str]:
    for n in names:
        if n in t.c:
            return n
    return None


def _normalize_doc_ids(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        # JSON list?
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if x]
            except Exception:
                pass
        return [s]
    return [str(raw)]


def _extract_doc_fields(row: Dict[str, Any]) -> List[tuple[str, Any]]:
    keys = (
        "document_ids",
        "doc_ids",
        "documents",
        "attachments",
        "attachment_ids",
        "upload_ids",
        "document_refs",
        "document_id",
        "doc_id",
        "upload_id",
    )
    out = []
    for k in keys:
        if k in row and row[k] is not None:
            out.append((k, row[k]))
    return out


def _approved_doc_ids(db: Session, ids: List[str]) -> Set[str]:
    if not ids:
        return set()

    t = _documents_table(db)
    if t is None:
        return set()

    id_col = _pick_col(t, ("id", "document_id", "upload_id"))
    status_col = _pick_col(t, ("status", "state", "review_status", "quarantine_status"))
    if id_col is None or status_col is None:
        return set()

    ok_values = {"approved", "APPROVED", "ok", "OK"}
    rows = db.execute(select(t.c[id_col], t.c[status_col]).where(t.c[id_col].in_(ids))).mappings().all()

    approved: Set[str] = set()
    for r in rows:
        st = r.get(status_col)
        if st is None:
            continue
        if str(st) in ok_values:
            approved.add(str(r[id_col]))
    return approved


def _filter_row_docs_to_approved(db: Session, row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Konservativ: wenn wir doc-status nicht auflösen können, liefern wir KEINE docs aus.
    Das entspricht Quarantine-by-default.
    """
    doc_fields = _extract_doc_fields(row)
    if not doc_fields:
        return row

    all_ids: List[str] = []
    for _, v in doc_fields:
        all_ids.extend(_normalize_doc_ids(v))

    approved = _approved_doc_ids(db, list(set(all_ids)))

    out = dict(row)
    for k, v in doc_fields:
        ids = _normalize_doc_ids(v)
        keep = [x for x in ids if x in approved]

        if k in {"document_id", "doc_id", "upload_id"}:
            out[k] = keep[0] if keep else None
        else:
            out[k] = json.dumps(keep, ensure_ascii=False, separators=(",", ":"))
    return out


def _fetch_servicebook_entries(db: Session, servicebook_id: str) -> List[Dict[str, Any]]:
    t = _servicebook_entries_table(db)

    if "servicebook_id" in t.c:
        where_col = t.c.servicebook_id
    elif "vehicle_id" in t.c:
        where_col = t.c.vehicle_id
    elif "id" in t.c:
        where_col = t.c.id
    else:
        raise HTTPException(status_code=500, detail="servicebook_id_column_missing")

    rows = db.execute(select(t).where(where_col == servicebook_id)).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="not_found")

    return [dict(r) for r in rows]


def _enforce_scope_or_admin(actor: Any, rows: List[Dict[str, Any]]) -> None:
    role = _actor_role(actor)

    if role in {"admin", "superadmin"}:
        return

    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    actor_uid = _actor_user_id(actor)
    if not actor_uid:
        raise HTTPException(status_code=403, detail="forbidden")

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

    # Quarantine-by-default: only approved doc refs in redacted export
    rows = [_filter_row_docs_to_approved(db, r) for r in rows]

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
