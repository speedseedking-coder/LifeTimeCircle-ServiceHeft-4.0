from __future__ import annotations

import base64
import datetime as dt
import importlib
import inspect as pyinspect
import json
import uuid
from hashlib import sha256
from typing import Any, Dict, Optional, Tuple, Type

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.auth.crypto import token_hash as token_hash_fn
from app.core.config import get_settings
from app.core.security import Actor, require_roles
from app.db.session import get_db
from app.models.audit import IdempotencyRecord

router = APIRouter(prefix="/export", tags=["export"])


# ---------------------------
# helpers: time / json
# ---------------------------

def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)


def _dt_iso(x: Optional[dt.datetime]) -> Optional[str]:
    if x is None:
        return None
    if x.tzinfo is None:
        x = x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(dt.timezone.utc).isoformat()


# ---------------------------
# helpers: "best effort" audit
# ---------------------------

def _emit_best_effort_audit_event(
    db: Session,
    *,
    actor: Actor,
    event_name: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = None,
) -> None:
    """
    Best-effort: Audit darf Export nicht killen.
    Nutzt (wenn vorhanden) app.services.masterclipboard.emit_event,
    weil dort bereits AuditEvent + Idempotency sauber umgesetzt ist.
    """
    try:
        mod = importlib.import_module("app.services.masterclipboard")
        emit_event = getattr(mod, "emit_event", None)
        if emit_event is None:
            return
        emit_event(
            db=db,
            correlation_id=str(uuid.uuid4()),
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            event_name=event_name,
            payload={
                # keine Klartext-PII / kein Freitext
                "actor_id": getattr(actor, "sub", None) or getattr(actor, "user_id", None) or "unknown",
                "actor_role": getattr(actor, "role", None) or "unknown",
                **payload,
            },
        )
    except Exception:
        return


# ---------------------------
# helpers: export-token (TTL/Limit)
# ---------------------------

def _mint_full_export_token(*, actor: Actor, target_id: str, ttl_seconds: int) -> Tuple[str, str]:
    """
    Full-Export Token:
    - TTL über exp
    - Limit (1-use) über IdempotencyRecord beim Verbrauch
    """
    settings = get_settings()

    ttl = int(ttl_seconds)
    if ttl < 60:
        ttl = 60
    if ttl > 3600:
        ttl = 3600

    now = _utc_now()
    exp = now + dt.timedelta(seconds=ttl)
    jti = str(uuid.uuid4())

    payload = {
        "sub": "export_grant",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "scope": "masterclipboard_full_export",
        "target_id": target_id,
        "issuer": "ltc-serviceheft",
        "actor_role": getattr(actor, "role", None) or "unknown",
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, exp.isoformat()


def _decode_full_export_token(raw_token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(raw_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="export_token_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="export_token_invalid")

    if payload.get("scope") != "masterclipboard_full_export":
        raise HTTPException(status_code=403, detail="export_token_invalid_scope")
    if not payload.get("jti"):
        raise HTTPException(status_code=403, detail="export_token_missing_jti")
    if not payload.get("target_id"):
        raise HTTPException(status_code=403, detail="export_token_missing_target_id")

    return payload


def _consume_one_time_token(db: Session, *, jti: str, token_hmac: str) -> None:
    """
    One-time use via IdempotencyRecord – aber robust gegenüber abweichenden
    ORM-Attributnamen: wir inserten direkt in die Table-Columns.

    Token wird absichtlich VOR Datenzugriff konsumiert (least privilege).
    """
    tbl = IdempotencyRecord.__table__
    cols = {c.name for c in tbl.columns}

    values: Dict[str, Any] = {}

    # correlation / jti
    if "correlation_id" in cols:
        values["correlation_id"] = jti
    elif "correlationId" in cols:
        values["correlationId"] = jti
    elif "correlation" in cols:
        values["correlation"] = jti
    elif "request_id" in cols:
        values["request_id"] = jti
    elif "requestId" in cols:
        values["requestId"] = jti

    # idempotency
    if "idempotency_key" in cols:
        values["idempotency_key"] = token_hmac
    elif "idempotencyKey" in cols:
        values["idempotencyKey"] = token_hmac
    elif "idem_key" in cols:
        values["idem_key"] = token_hmac

    # event name
    if "event_name" in cols:
        values["event_name"] = "export.full.token_used"
    elif "eventName" in cols:
        values["eventName"] = "export.full.token_used"
    elif "event" in cols:
        values["event"] = "export.full.token_used"

    # created timestamp (wenn vorhanden)
    now = _utc_now()
    if "created_at" in cols:
        values["created_at"] = now
    elif "createdAt" in cols:
        values["createdAt"] = now
    elif "at" in cols:
        values["at"] = now

    # Wenn die Tabelle zwingend mehr NOT NULL Felder hat, würden wir hier eh
    # einen DB-Fehler bekommen – dann sehen wir den konkreten Spaltennamen im Trace.
    try:
        db.execute(insert(tbl).values(**values))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="export_token_already_used")


# ---------------------------
# helpers: model discovery + safe serialization
# ---------------------------

def _find_first_model_class(module_path: str, table_name_hint: str) -> Type[Any]:
    """
    Findet in einem Modul die erste Klasse mit __tablename__ und Hint.
    """
    mod = importlib.import_module(module_path)
    candidates: list[Type[Any]] = []
    for _, obj in vars(mod).items():
        if not pyinspect.isclass(obj):
            continue
        tn = getattr(obj, "__tablename__", None)
        if isinstance(tn, str) and table_name_hint.lower() in tn.lower():
            candidates.append(obj)

    if not candidates:
        raise HTTPException(status_code=500, detail="export_model_not_found")

    return candidates[0]


def _get_row_by_any_key(db: Session, model: Type[Any], key_value: str) -> Optional[Any]:
    """
    Robust: versucht PK-get, danach typische Spaltennamen.
    """
    try:
        row = db.get(model, key_value)
        if row is not None:
            return row
    except Exception:
        pass

    for col in ("id", "session_id", "masterclipboard_id", "clipboard_id", "uuid"):
        if hasattr(model, col):
            try:
                stmt = select(model).where(getattr(model, col) == key_value)  # type: ignore[operator]
                row = db.execute(stmt).scalars().first()
                if row is not None:
                    return row
            except Exception:
                continue

    return None


def _sa_obj_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Serialisiert NUR echte Column-Attrs (keine Relationships).
    """
    out: Dict[str, Any] = {}
    insp = sa_inspect(obj)
    for attr in insp.mapper.column_attrs:
        k = attr.key
        v = getattr(obj, k)
        if isinstance(v, dt.datetime):
            out[k] = _dt_iso(v)
        elif isinstance(v, bytes):
            out[k] = base64.b64encode(v).decode("ascii")
        else:
            out[k] = v
    return out


def _redact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Konservative Redaction: alles, was nach Freitext/PII aussehen könnte, fliegt raus.
    """
    drop_contains = (
        "email", "phone", "tel", "name", "address", "street", "zip", "city",
        "vin", "kennzeichen", "plate", "license",
        "gps", "geo", "lat", "lng",
        "note", "comment", "text", "speech", "transcript", "raw",
        "file", "image", "photo", "audio",
        "reason",
        "token", "secret", "password",
    )

    out: Dict[str, Any] = {}
    for k, v in d.items():
        kl = (k or "").lower()
        if any(x in kl for x in drop_contains):
            continue
        if isinstance(v, dict):
            out[k] = _redact_dict(v)
        elif isinstance(v, list):
            out[k] = [_redact_dict(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


# ---------------------------
# helpers: encryption (Full Export)
# ---------------------------

def _derive_fernet_key(secret_key: str) -> bytes:
    digest = sha256((secret_key + "|export|full").encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt_full_payload(secret_key: str, payload: Dict[str, Any]) -> str:
    """
    Strong encryption via cryptography.Fernet.
    Wenn cryptography fehlt: bewusst blocken (Policy fordert Verschlüsselung).
    """
    try:
        from cryptography.fernet import Fernet  # type: ignore
    except Exception:
        raise HTTPException(status_code=501, detail="encryption_unavailable")

    key = _derive_fernet_key(secret_key)
    f = Fernet(key)
    token = f.encrypt(_json_dumps(payload).encode("utf-8"))
    return token.decode("utf-8")


# ---------------------------
# endpoints
# ---------------------------

@router.get("/masterclipboard/{masterclipboard_id}")
def export_masterclipboard_redacted(
    masterclipboard_id: str,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles("dealer", "admin")),
) -> Dict[str, Any]:
    """
    Redacted Export: nur dealer/admin (wie Masterclipboard-API).
    Keine Klartext-PII, kein Freitext.
    """
    model = _find_first_model_class("app.models.masterclipboard", "masterclipboard")
    row = _get_row_by_any_key(db, model, masterclipboard_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")

    raw = _sa_obj_to_dict(row)
    red = _redact_dict(raw)

    _emit_best_effort_audit_event(
        db,
        actor=actor,
        event_name="export.event.masterclipboard_redacted",
        payload={"target_id": masterclipboard_id, "result": "success"},
    )

    return {
        "meta": {
            "export_type": "masterclipboard",
            "mode": "redacted",
            "generated_at": _utc_now().isoformat(),
        },
        "data": red,
    }


@router.post("/masterclipboard/{masterclipboard_id}/grant")
def grant_masterclipboard_full_export(
    masterclipboard_id: str,
    ttl_seconds: int = 900,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles("superadmin")),
) -> Dict[str, Any]:
    """
    Full Export Grant:
    - nur SUPERADMIN
    - TTL via exp
    - Limit via one-time consumption (IdempotencyRecord)
    """
    token, expires_at = _mint_full_export_token(actor=actor, target_id=masterclipboard_id, ttl_seconds=ttl_seconds)

    _emit_best_effort_audit_event(
        db,
        actor=actor,
        event_name="export.event.full_grant_issued",
        payload={"target_id": masterclipboard_id, "result": "success"},
        idempotency_key=str(uuid.uuid4()),
    )

    return {
        "export_token": token,
        "expires_at": expires_at,
        "mode": "full_encrypted",
        "note": "Token ist one-time + TTL. Nicht loggen, nicht speichern in Klartext.",
    }


@router.get("/masterclipboard/{masterclipboard_id}/full")
def export_masterclipboard_full_encrypted(
    masterclipboard_id: str,
    x_export_token: Optional[str] = Header(default=None, alias="X-Export-Token"),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles("superadmin")),
) -> Dict[str, Any]:
    """
    Full Export:
    - nur SUPERADMIN
    - zusätzlich X-Export-Token (TTL + one-time)
    - Payload ist verschlüsselt (Fernet)
    """
    if not x_export_token:
        raise HTTPException(status_code=400, detail="missing_export_token")

    claims = _decode_full_export_token(x_export_token)
    if str(claims.get("target_id")) != str(masterclipboard_id):
        raise HTTPException(status_code=403, detail="export_token_target_mismatch")

    settings = get_settings()
    token_h = token_hash_fn(settings.secret_key, x_export_token)

    # one-time consumption (vor Datenzugriff)
    _consume_one_time_token(db, jti=str(claims["jti"]), token_hmac=token_h)

    model = _find_first_model_class("app.models.masterclipboard", "masterclipboard")
    row = _get_row_by_any_key(db, model, masterclipboard_id)
    if row is None:
        _emit_best_effort_audit_event(
            db,
            actor=actor,
            event_name="export.event.masterclipboard_full",
            payload={"target_id": masterclipboard_id, "result": "not_found"},
            idempotency_key=token_h,
        )
        raise HTTPException(status_code=404, detail="not_found")

    raw = _sa_obj_to_dict(row)
    payload = {
        "meta": {
            "export_type": "masterclipboard",
            "mode": "full_encrypted",
            "generated_at": _utc_now().isoformat(),
        },
        "data": raw,
    }

    ciphertext = _encrypt_full_payload(settings.secret_key, payload)

    _emit_best_effort_audit_event(
        db,
        actor=actor,
        event_name="export.event.masterclipboard_full",
        payload={"target_id": masterclipboard_id, "result": "success"},
        idempotency_key=token_h,
    )

    return {
        "meta": {
            "export_type": "masterclipboard",
            "mode": "full_encrypted",
            "generated_at": _utc_now().isoformat(),
            "cipher": "fernet",
        },
        "ciphertext": ciphertext,
    }
