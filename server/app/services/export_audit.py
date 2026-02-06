import datetime as dt
import json
from typing import Any, Dict, Optional

from sqlalchemy import MetaData, Table, Column, String, DateTime, Boolean, insert
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _safe_json(meta: Optional[Dict[str, Any]]) -> str:
    if not meta:
        return "{}"
    return json.dumps(meta, ensure_ascii=False, separators=(",", ":"))


def _pick_audit_table(db: Session) -> Table:
    # WICHTIG: gleiche Connection nutzen (sqlite :memory: safe)
    conn = db.connection()
    insp = sa_inspect(conn)
    md = MetaData()

    for name in ("audit_events", "audit", "audits"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=conn)

    # Fallback (nur wenn gar nichts existiert)
    fallback = "export_audit_events"
    t = Table(
        fallback,
        md,
        Column("id", String(64), primary_key=True),
        Column("event_type", String(64), nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("actor_role", String(32), nullable=False),
        Column("actor_user_id", String(128), nullable=True),
        Column("target_type", String(32), nullable=False),
        Column("target_id", String(128), nullable=False),
        Column("success", Boolean, nullable=False),
        Column("reason", String(128), nullable=True),
        Column("meta_json", String, nullable=False),
    )
    md.create_all(bind=conn, tables=[t], checkfirst=True)
    return t


def write_export_audit(
    db: Session,
    *,
    event_type: str,
    actor_role: str,
    actor_user_id: Optional[str],
    target_type: str,
    target_id: str,
    success: bool,
    reason: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Audit ohne Klartext-PII/Secrets.
    Token wird NIE geloggt.
    """
    t = _pick_audit_table(db)
    now = _utcnow()

    payload = {
        "id": f"exp_{int(now.timestamp())}_{now.microsecond}",
        "event_type": event_type,
        "created_at": now,
        "actor_role": actor_role,
        "actor_user_id": actor_user_id,
        "target_type": target_type,
        "target_id": target_id,
        "success": bool(success),
        "reason": reason,
        "meta_json": _safe_json(meta),
    }

    cols = set(t.columns.keys())
    filtered = {k: v for k, v in payload.items() if k in cols}

    # häufige Alternativnamen abfangen
    if "ts" in cols and "ts" not in filtered:
        filtered["ts"] = now
    if "created" in cols and "created" not in filtered:
        filtered["created"] = now
    if "type" in cols and "type" not in filtered:
        filtered["type"] = event_type

    try:
        db.execute(insert(t).values(**filtered))
        db.commit()
    except Exception:
        db.rollback()
