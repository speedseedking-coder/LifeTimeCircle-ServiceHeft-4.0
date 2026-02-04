# server/app/services/servicebook_store.py
from __future__ import annotations

import datetime as dt
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import HTTPException
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    insert,
    select,
    update,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import Integer as SAInteger, BigInteger as SABigInteger


# ---------------------------
# helpers: actor
# ---------------------------
def actor_role(actor: Any) -> str:
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


def actor_user_id(actor: Any) -> Optional[str]:
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


# ---------------------------
# DB autodetect (entries)
# ---------------------------
def _dialect_name(db: Session) -> str:
    try:
        conn = db.connection()
        return str(getattr(conn, "dialect", None).name)
    except Exception:
        try:
            return str(getattr(db.bind, "dialect", None).name)
        except Exception:
            return ""


def _allow_bootstrap(db: Session) -> bool:
    """
    Safety:
    - In Tests/Dev (SQLite) erlauben wir Auto-Create, damit das Feature überhaupt läuft.
    - In Prod NICHT automatisch (außer explizit über Env-Flag).
    """
    if os.getenv("LTC_AUTO_CREATE_SERVICEBOOK_TABLE", "").strip() == "1":
        return True

    d = _dialect_name(db).lower()
    if d == "sqlite":
        return True

    return False


def _create_servicebook_entries_table(db: Session, name: str) -> Table:
    """
    Minimal-MVP Tabelle für Servicebook Entries.
    (Migration kann später sauber nachgezogen werden.)
    """
    conn = db.connection()
    md = MetaData()

    t = Table(
        name,
        md,
        Column("id", String(36), primary_key=True, nullable=False),
        Column("servicebook_id", String(64), nullable=False, index=True),
        Column("owner_id", String(64), nullable=True, index=True),
        Column("actor_role", String(32), nullable=True),
        Column("entry_type", String(64), nullable=True, index=True),
        Column("source", String(32), nullable=True),
        Column("result_status", String(32), nullable=True, index=True),
        Column("title", String(255), nullable=True),
        Column("summary", Text, nullable=True),
        Column("details", Text, nullable=True),
        Column("occurred_at", DateTime(timezone=True), nullable=True, index=True),
        Column("km", Integer, nullable=True),
        Column("document_ids", Text, nullable=True),  # JSON list
        Column("related_entry_id", String(64), nullable=True, index=True),
        Column("related_case_id", String(64), nullable=True, index=True),
        Column("created_at", DateTime(timezone=True), nullable=True, index=True),
        Column("updated_at", DateTime(timezone=True), nullable=True, index=True),
    )

    t.create(bind=conn, checkfirst=True)
    return Table(name, MetaData(), autoload_with=conn)


def servicebook_entries_table(db: Session) -> Table:
    """
    Servicebook ist evtl. noch nicht als Model vorhanden => Table autodetect.
    Wenn keine Tabelle existiert:
      - SQLite/Test: auto-create
      - sonst: 404 servicebook_table_missing
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

    if _allow_bootstrap(db):
        # Canonical table name:
        return _create_servicebook_entries_table(db, "servicebook_entries")

    raise HTTPException(status_code=404, detail="servicebook_table_missing")


def _pick_col(t: Table, names: Sequence[str]) -> Optional[str]:
    for n in names:
        if n in t.c:
            return n
    return None


def _link_col_for_servicebook_id(t: Table) -> Tuple[str, str]:
    if "servicebook_id" in t.c:
        return ("servicebook_id", "servicebook_id")
    if "vehicle_id" in t.c:
        return ("vehicle_id", "vehicle_id")
    raise HTTPException(status_code=500, detail="servicebook_id_column_missing")


def _ensure_id_if_needed(values: Dict[str, Any], t: Table) -> None:
    """
    Integer PK: nicht anfassen.
    String PK ohne Default und not-null: UUID setzen.
    """
    if "id" not in t.c:
        return
    if "id" in values:
        return

    col = t.c["id"]

    # integer-ish => DB macht das
    try:
        if isinstance(col.type, (SAInteger, SABigInteger, Integer, BigInteger)):
            return
    except Exception:
        pass

    if getattr(col, "nullable", True) is True:
        return
    if getattr(col, "server_default", None) is not None:
        return
    if getattr(col, "default", None) is not None:
        return

    values["id"] = str(uuid.uuid4())


def _json_dump(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def _maybe_set(values: Dict[str, Any], t: Table, col_candidates: Sequence[str], v: Any) -> None:
    c = _pick_col(t, col_candidates)
    if c is not None and v is not None:
        values[c] = v


def _best_effort_doc_field(t: Table) -> Optional[str]:
    return _pick_col(
        t,
        (
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
        ),
    )


# ---------------------------
# Scope
# ---------------------------
def fetch_entries(db: Session, servicebook_id: str) -> List[Dict[str, Any]]:
    t = servicebook_entries_table(db)
    _, where_col_name = _link_col_for_servicebook_id(t)
    where_col = t.c[where_col_name]

    rows = db.execute(select(t).where(where_col == servicebook_id)).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="not_found")
    return [dict(r) for r in rows]


def enforce_scope_or_admin(actor: Any, rows: List[Dict[str, Any]]) -> None:
    role = actor_role(actor)
    if role in {"admin", "superadmin"}:
        return

    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    uid = actor_user_id(actor)
    if not uid:
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
                if str(row[k]) == str(uid):
                    return

    raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------
# CRUD: entries
# ---------------------------
def create_entry(
    db: Session,
    servicebook_id: str,
    actor: Any,
    *,
    entry_type: str,
    source: str,
    result_status: str,
    title: Optional[str],
    summary: Optional[str],
    details: Optional[str],
    occurred_at: Optional[dt.datetime],
    km: Optional[int],
    document_ids: Optional[List[str]],
    related_entry_id: Optional[str],
    related_case_id: Optional[str],
) -> Dict[str, Any]:
    t = servicebook_entries_table(db)
    _, link_col = _link_col_for_servicebook_id(t)

    values: Dict[str, Any] = {}
    values[link_col] = servicebook_id

    _ensure_id_if_needed(values, t)

    uid = actor_user_id(actor)
    _maybe_set(values, t, ("owner_id", "user_id", "created_by_user_id", "created_by", "actor_user_id"), uid)
    _maybe_set(values, t, ("actor_role", "role"), actor_role(actor))

    now = dt.datetime.now(dt.timezone.utc)
    _maybe_set(values, t, ("created_at", "created", "created_on"), now)
    _maybe_set(values, t, ("updated_at", "updated", "updated_on"), now)

    if occurred_at is not None:
        _maybe_set(values, t, ("occurred_at", "event_at", "date", "happened_at"), occurred_at)

    if km is not None:
        _maybe_set(values, t, ("km", "mileage", "odometer_km"), km)

    _maybe_set(values, t, ("entry_type", "type", "kind", "category"), entry_type)
    _maybe_set(values, t, ("source", "origin", "module"), source)
    _maybe_set(values, t, ("result_status", "status", "result"), result_status)

    if title is not None:
        _maybe_set(values, t, ("title", "headline", "name"), title)
    if summary is not None:
        _maybe_set(values, t, ("summary", "short", "note"), summary)
    if details is not None:
        _maybe_set(values, t, ("details", "description", "body", "text"), details)

    if related_entry_id is not None:
        _maybe_set(values, t, ("related_entry_id", "parent_entry_id", "ref_entry_id"), related_entry_id)
    if related_case_id is not None:
        _maybe_set(values, t, ("related_case_id", "case_id", "ref_case_id"), related_case_id)

    if document_ids is not None:
        doc_field = _best_effort_doc_field(t)
        if doc_field is not None:
            if doc_field in {"document_id", "doc_id", "upload_id"}:
                values[doc_field] = document_ids[0] if document_ids else None
            else:
                values[doc_field] = _json_dump(document_ids)

    res = db.execute(insert(t).values(**values))
    db.commit()

    inserted_id = None
    try:
        pk = res.inserted_primary_key
        if pk and pk[0] is not None:
            inserted_id = str(pk[0])
    except Exception:
        inserted_id = None

    if inserted_id and "id" in t.c:
        row = db.execute(select(t).where(t.c.id == inserted_id)).mappings().first()
        if row:
            return dict(row)

    rows = db.execute(select(t).where(t.c[link_col] == servicebook_id)).mappings().all()
    if not rows:
        raise HTTPException(status_code=500, detail="insert_failed")
    return dict(rows[-1])


def update_entry_best_effort(db: Session, entry_id: str, patch: Dict[str, Any]) -> None:
    t = servicebook_entries_table(db)
    if "id" not in t.c:
        return

    safe_patch = {k: v for k, v in patch.items() if k in t.c}
    if not safe_patch:
        return

    now = dt.datetime.now(dt.timezone.utc)
    for k in ("updated_at", "updated", "updated_on"):
        if k in t.c and k not in safe_patch:
            safe_patch[k] = now
            break

    db.execute(update(t).where(t.c.id == entry_id).values(**safe_patch))
    db.commit()
