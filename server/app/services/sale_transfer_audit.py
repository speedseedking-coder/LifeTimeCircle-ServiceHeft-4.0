from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, insert
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _pick_audit_table(db: Session) -> Table:
    bind = db.get_bind()
    if bind is None:
        raise RuntimeError("DB bind fehlt")

    insp = sa_inspect(bind)
    md = MetaData()

    for name in ("audit_events", "audit", "audits"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=bind)

    name = "sale_transfer_audit_events"
    if insp.has_table(name):
        return Table(name, md, autoload_with=bind)

    t = Table(
        name,
        md,
        Column("event_id", String(36), primary_key=True),
        Column("at", DateTime(timezone=True), nullable=False, index=True),
        Column("event_type", String(64), nullable=False, index=True),
        Column("actor_id", String(64), nullable=True, index=True),
        Column("target_id", String(64), nullable=True, index=True),
        Column("payload_json", Text, nullable=True),
    )
    md.create_all(bind=bind)
    return t


def write_sale_audit(
    db: Session,
    *,
    event_type: str,
    actor_user_id: str,
    target_id: str,
    payload: Dict[str, Any],
) -> None:
    t = _pick_audit_table(db)
    now = _utc_now()
    cols = set(c.name for c in t.c)

    values: Dict[str, Any] = {}

    if "event_id" in cols:
        values["event_id"] = str(uuid.uuid4())
    elif "id" in cols:
        values["id"] = str(uuid.uuid4())

    if "at" in cols:
        values["at"] = now
    elif "created_at" in cols:
        values["created_at"] = now
    elif "timestamp" in cols:
        values["timestamp"] = now

    if "event_name" in cols:
        values["event_name"] = event_type
    elif "event_type" in cols:
        values["event_type"] = event_type
    elif "action" in cols:
        values["action"] = event_type

    if "actor_id" in cols:
        values["actor_id"] = actor_user_id
    elif "actor_user_id" in cols:
        values["actor_user_id"] = actor_user_id

    if "target_id" in cols:
        values["target_id"] = target_id
    elif "resource_id" in cols:
        values["resource_id"] = target_id

    if "result" in cols and "result" not in values:
        values["result"] = "success"

    if "correlation_id" in cols:
        values["correlation_id"] = str(uuid.uuid4())
    if "idempotency_key" in cols:
        values["idempotency_key"] = "n/a"

    if "payload_json" in cols:
        values["payload_json"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif "details_json" in cols:
        values["details_json"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif "details" in cols:
        values["details"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    db.execute(insert(t).values(**values))