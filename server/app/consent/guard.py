# server/app/consent/guard.py
from __future__ import annotations

import importlib
import inspect
from typing import Any, Optional

from fastapi import Depends, HTTPException

# project-safe db/actor deps (in diesem Repo existiert export_vehicle sicher)
from app.routers.export_vehicle import get_db, get_actor  # type: ignore


def _actor_get(actor: Any, key: str) -> Any:
    if actor is None:
        return None
    if isinstance(actor, dict):
        return actor.get(key)
    return getattr(actor, key, None)


def _extract_bool(maybe: Any) -> Optional[bool]:
    if isinstance(maybe, bool):
        return maybe
    return None


def _status_accepted(status: Any) -> Optional[bool]:
    """
    Erwartet bei /consent/status typischerweise accepted/is_accepted o.ä.
    """
    if isinstance(status, dict):
        for k in ("accepted", "is_accepted", "consent_accepted"):
            v = _extract_bool(status.get(k))
            if v is not None:
                return v
        # negatives Signal priorisieren
        for k in ("needs_reconsent", "reconsent_required", "consent_required"):
            v = _extract_bool(status.get(k))
            if v is True:
                return False
    return None


async def _call_status_fn(fn: Any, *, db: Any, actor: Any) -> Any:
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    for name, p in sig.parameters.items():
        if name in ("db", "session"):
            kwargs[name] = db
        elif name in ("actor", "current_actor", "user"):
            kwargs[name] = actor
        elif name in ("user_id", "uid"):
            uid = _actor_get(actor, "user_id") or _actor_get(actor, "id")
            kwargs[name] = uid
        else:
            # unknown param -> nur wenn default vorhanden, sonst skip (TypeError)
            if p.default is inspect._empty:
                raise TypeError("unsupported_signature")
    out = fn(**kwargs)
    if inspect.isawaitable(out):
        return await out
    return out


async def _get_consent_status(*, db: Any, actor: Any) -> Any:
    """
    Robust: versucht in typischen Consent-Modulen eine Status-Funktion zu finden.
    deny-by-default: wenn nichts gefunden/interpretierbar -> 403 consent_required
    """
    candidates = [
        ("app.routers.consent", ("consent_status", "get_status", "status")),
        ("app.consent.service", ("consent_status", "get_status", "get_consent_status", "status")),
        ("app.consent", ("consent_status", "get_status", "get_consent_status", "status")),
    ]

    last_exc: Optional[Exception] = None
    for mod_name, fn_names in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:  # pragma: no cover
            last_exc = e
            continue

        for fn_name in fn_names:
            fn = getattr(mod, fn_name, None)
            if not callable(fn):
                continue
            try:
                return await _call_status_fn(fn, db=db, actor=actor)
            except HTTPException:
                raise
            except Exception as e:  # pragma: no cover
                last_exc = e
                continue

    if last_exc:
        # kein Leak: keine Details nach außen
        pass
    raise HTTPException(status_code=403, detail="consent_required")


async def require_consent(db: Any = Depends(get_db), actor: Any = Depends(get_actor)) -> None:
    status = await _get_consent_status(db=db, actor=actor)
    accepted = _status_accepted(status)

    # deny-by-default
    if accepted is True:
        return

    # falls Status-Objekt nicht interpretierbar ist: ebenfalls deny
    raise HTTPException(status_code=403, detail="consent_required")