import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import Actor
from app.models.audit import AuditEvent, IdempotencyRecord
from app.models.masterclipboard import (
    MasterClipboardSession,
    MasterClipboardSpeechChunk,
    MasterClipboardTriageItem,
    MasterClipboardBoardSnapshot,
)


MODULE_ID = "masterclipboard"
SCHEMA_VERSION = "v1"


def _ensure_same_org(actor: Actor, session: MasterClipboardSession) -> None:
    if session.org_id != actor.org_id:
        raise PermissionError("forbidden")


def _idem_key(route_key: str, idempotency_key: str) -> str:
    # route_key + idempotency -> global unique record
    return f"{MODULE_ID}:{route_key}:{idempotency_key}"


def _load_idempotency(db: Session, route_key: str, idempotency_key: str):
    key = _idem_key(route_key, idempotency_key)
    rec = db.execute(select(IdempotencyRecord).where(IdempotencyRecord.key == key)).scalar_one_or_none()
    return rec


def _store_idempotency(db: Session, route_key: str, idempotency_key: str, status_code: int, response_obj: dict):
    key = _idem_key(route_key, idempotency_key)
    rec = IdempotencyRecord(key=key, status_code=status_code, response_json=json.dumps(response_obj, ensure_ascii=False))
    db.add(rec)


def emit_event(
    db: Session,
    *,
    event_name: str,
    correlation_id: str,
    idempotency_key: str,
    actor: Actor,
    payload: dict,
) -> None:
    ev = AuditEvent(
        module_id=MODULE_ID,
        event_name=event_name,
        schema_version=SCHEMA_VERSION,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        actor_role=actor.role,
        actor_subject_id=actor.subject_id,
        actor_scope_ref=actor.org_id,
        payload_json=AuditEvent.dump_payload(payload),
    )
    db.add(ev)


def create_session(db: Session, actor: Actor, vehicle_public_id: str, idempotency_key: str):
    existing = _load_idempotency(db, "sessions.create", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = MasterClipboardSession(org_id=actor.org_id, vehicle_public_id=vehicle_public_id)
    db.add(s)
    db.flush()  # s.id

    emit_event(
        db,
        event_name="masterclipboard.event.session_started",
        correlation_id=s.id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": s.id, "vehicle_public_id": vehicle_public_id},
    )

    resp = {"session_id": s.id}
    _store_idempotency(db, "sessions.create", idempotency_key, 201, resp)
    return 201, resp


def add_speech_chunk(db: Session, actor: Actor, session_id: str, source: str, content_redacted: str, idempotency_key: str):
    existing = _load_idempotency(db, f"{session_id}.speech.add", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = db.get(MasterClipboardSession, session_id)
    if not s:
        return 404, {"error": "not_found"}
    _ensure_same_org(actor, s)
    if s.is_closed:
        return 409, {"error": "session_closed"}

    ch = MasterClipboardSpeechChunk(session_id=session_id, source=source, content_redacted=content_redacted)
    db.add(ch)
    db.flush()

    emit_event(
        db,
        event_name="masterclipboard.event.speech_chunk_added",
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": session_id, "speech_chunk_id": ch.id, "source": source},
    )

    resp = {"speech_chunk_id": ch.id}
    _store_idempotency(db, f"{session_id}.speech.add", idempotency_key, 201, resp)
    return 201, resp


def create_triage_items(db: Session, actor: Actor, session_id: str, items: list[dict], idempotency_key: str):
    existing = _load_idempotency(db, f"{session_id}.triage.create", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = db.get(MasterClipboardSession, session_id)
    if not s:
        return 404, {"error": "not_found"}
    _ensure_same_org(actor, s)
    if s.is_closed:
        return 409, {"error": "session_closed"}

    created_ids: list[str] = []
    for it in items:
        ev_refs = it.get("evidence_refs")
        ev_json = json.dumps(ev_refs, ensure_ascii=False) if ev_refs else None
        tri = MasterClipboardTriageItem(
            session_id=session_id,
            kind=it["kind"],
            title=it["title"],
            details_redacted=it.get("details_redacted"),
            severity=it["severity"],
            status=it["status"],
            evidence_refs_json=ev_json,
        )
        db.add(tri)
        db.flush()
        created_ids.append(tri.id)

    emit_event(
        db,
        event_name="masterclipboard.event.triage_item_created",
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": session_id, "created_ids": created_ids},
    )

    resp = {"created_ids": created_ids}
    _store_idempotency(db, f"{session_id}.triage.create", idempotency_key, 201, resp)
    return 201, resp


def patch_triage_item(db: Session, actor: Actor, session_id: str, item_id: str, patch: dict, idempotency_key: str):
    existing = _load_idempotency(db, f"{session_id}.triage.patch.{item_id}", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = db.get(MasterClipboardSession, session_id)
    if not s:
        return 404, {"error": "not_found"}
    _ensure_same_org(actor, s)
    if s.is_closed:
        return 409, {"error": "session_closed"}

    tri = db.get(MasterClipboardTriageItem, item_id)
    if not tri or tri.session_id != session_id:
        return 404, {"error": "not_found"}

    if patch.get("title") is not None:
        tri.title = patch["title"]
    if patch.get("details_redacted") is not None:
        tri.details_redacted = patch["details_redacted"]
    if patch.get("severity") is not None:
        tri.severity = patch["severity"]
    if patch.get("status") is not None:
        tri.status = patch["status"]

    tri.updated_at = datetime.utcnow()

    emit_event(
        db,
        event_name="masterclipboard.event.triage_item_updated",
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": session_id, "item_id": item_id},
    )

    resp = {"ok": True}
    _store_idempotency(db, f"{session_id}.triage.patch.{item_id}", idempotency_key, 200, resp)
    return 200, resp


def create_board_snapshot(db: Session, actor: Actor, session_id: str, ordered_item_ids: list[str], notes_redacted: str | None, idempotency_key: str):
    existing = _load_idempotency(db, f"{session_id}.board.snapshot", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = db.get(MasterClipboardSession, session_id)
    if not s:
        return 404, {"error": "not_found"}
    _ensure_same_org(actor, s)
    if s.is_closed:
        return 409, {"error": "session_closed"}

    snap = MasterClipboardBoardSnapshot(
        session_id=session_id,
        ordered_item_ids_json=json.dumps(ordered_item_ids, ensure_ascii=False),
        notes_redacted=notes_redacted,
    )
    db.add(snap)
    db.flush()

    emit_event(
        db,
        event_name="masterclipboard.event.board_snapshot",
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": session_id, "snapshot_id": snap.id, "ordered_item_ids": ordered_item_ids},
    )

    resp = {"snapshot_id": snap.id}
    _store_idempotency(db, f"{session_id}.board.snapshot", idempotency_key, 201, resp)
    return 201, resp


def close_session(db: Session, actor: Actor, session_id: str, idempotency_key: str):
    existing = _load_idempotency(db, f"{session_id}.close", idempotency_key)
    if existing:
        return existing.status_code, json.loads(existing.response_json)

    s = db.get(MasterClipboardSession, session_id)
    if not s:
        return 404, {"error": "not_found"}
    _ensure_same_org(actor, s)

    if not s.is_closed:
        s.is_closed = True
        s.closed_at = datetime.utcnow()

    emit_event(
        db,
        event_name="masterclipboard.event.session_closed",
        correlation_id=session_id,
        idempotency_key=idempotency_key,
        actor=actor,
        payload={"session_id": session_id},
    )

    resp = {"ok": True}
    _store_idempotency(db, f"{session_id}.close", idempotency_key, 200, resp)
    return 200, resp
