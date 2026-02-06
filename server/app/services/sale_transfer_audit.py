from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, insert
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

# Fallback-table (sale_transfer-spezifisch)
name = "sale_transfer_audit_events"
MODULE_ID = "sale_transfer"


def _utc_now() -> datetime:
    # naive UTC (SQLite-friendly) – ohne datetime.utcnow() (DeprecationWarning)
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)


def _get_engine(db: Session) -> Engine:
    bind = db.get_bind()
    if isinstance(bind, Engine):
        return bind
    if isinstance(bind, Connection):
        return bind.engine
    raise RuntimeError("DB bind ist weder Engine noch Connection")


def _json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _ensure_fallback_table(engine: Engine) -> Table:
    """
    Wenn Tabelle existiert: autoload (damit Schema-Mismatch nicht crasht).
    Wenn nicht: anlegen mit unseren Spalten.
    """
    insp = sa_inspect(engine)
    md = MetaData()

    if name in set(insp.get_table_names()):
        return Table(name, md, autoload_with=engine)

    t = Table(
        name,
        md,
        Column("id", String(36), primary_key=True),
        Column("at", DateTime, nullable=False),
        Column("event_type", String(64), nullable=False),
        Column("module_id", String(64), nullable=False),
        Column("actor_user_id", String(64), nullable=True),
        Column("target_id", String(64), nullable=True),
        Column("correlation_id", String(64), nullable=True),
        Column("idempotency_key", String(128), nullable=True),
        Column("payload_json", Text, nullable=False),
    )
    md.create_all(engine, tables=[t], checkfirst=True)
    return t


def _pick_primary_table(engine: Engine) -> Optional[Table]:
    insp = sa_inspect(engine)
    tables = set(insp.get_table_names())
    md = MetaData()
    for candidate in ("audit_events", "audit", "audits"):
        if candidate in tables:
            return Table(candidate, md, autoload_with=engine)
    return None


def _build_values(
    t: Table,
    event_type: str,
    *,
    actor_user_id: Optional[str],
    target_id: Optional[str],
    correlation_id: Optional[str],
    idempotency_key: Optional[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    now = _utc_now()
    pj = _json(payload)

    cols = set(t.c.keys())
    v: Dict[str, Any] = {}

    # id / event_id
    if "id" in cols:
        v["id"] = str(uuid.uuid4())
    elif "event_id" in cols:
        v["event_id"] = str(uuid.uuid4())

    # time columns (best-effort)
    for k in ("at", "created_at", "occurred_at", "ts", "timestamp"):
        if k in cols:
            v[k] = now
            break

    # module_id ist oft NOT NULL -> immer setzen, wenn vorhanden
    for k in ("module_id", "module", "moduleId"):
        if k in cols:
            v[k] = MODULE_ID
            break

    # event name/type columns
    if "event_type" in cols:
        v["event_type"] = event_type
    if "event_name" in cols:
        v["event_name"] = event_type
    if "action" in cols:
        v["action"] = event_type

    # actor
    if actor_user_id:
        for k in ("actor_user_id", "actor_id", "user_id", "actor", "userId"):
            if k in cols:
                v[k] = actor_user_id
                break

    # target/entity
    if target_id:
        for k in ("target_id", "entity_id", "resource_id", "object_id", "target", "entityId"):
            if k in cols:
                v[k] = target_id
                break

    # correlation + idem
    if correlation_id:
        for k in ("correlation_id", "correlationId"):
            if k in cols:
                v[k] = correlation_id
                break
    if idempotency_key:
        for k in ("idempotency_key", "idempotencyKey"):
            if k in cols:
                v[k] = idempotency_key
                break

    # payload json field
    for k in ("payload_json", "details_json", "data_json", "payload"):
        if k in cols:
            v[k] = pj
            break

    return v


def write_sale_audit(
    db: Session,
    event_type: str,
    *,
    actor_user_id: Optional[str] = None,
    target_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Best-effort Audit: darf Sale/Transfer NICHT killen.
    Prefer existing audit_events/audit/audits; fallback auf sale_transfer_audit_events.
    """
    engine = _get_engine(db)
    payload = payload or {}

    primary = _pick_primary_table(engine)
    fallback = _ensure_fallback_table(engine)

    # 1) primary best-effort (eigene TX, damit Business-Session nicht kaputt geht)
    if primary is not None:
        try:
            values = _build_values(
                primary,
                event_type,
                actor_user_id=actor_user_id,
                target_id=target_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                payload=payload,
            )
            with engine.begin() as conn:
                conn.execute(insert(primary).values(**values))
            return
        except Exception:
            pass

    # 2) fallback best-effort
    try:
        values = _build_values(
            fallback,
            event_type,
            actor_user_id=actor_user_id,
            target_id=target_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )

        # Mindestfelder absichern (falls fallback minimal ist)
        cols = set(fallback.c.keys())
        if "id" in cols:
            values.setdefault("id", str(uuid.uuid4()))
        if "at" in cols:
            values.setdefault("at", _utc_now())
        if "event_type" in cols:
            values.setdefault("event_type", event_type)
        if "module_id" in cols:
            values.setdefault("module_id", MODULE_ID)
        if "payload_json" in cols:
            values.setdefault("payload_json", _json(payload))

        with engine.begin() as conn:
            conn.execute(insert(fallback).values(**values))
    except Exception:
        return
