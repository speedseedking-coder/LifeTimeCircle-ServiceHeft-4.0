# server/app/rbac.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request

from app.auth.service import (
    db,
    get_session_by_token_hash,
    init_db,
    load_settings as load_auth_settings,
    token_hash_fn,
)


@dataclass(frozen=True)
class Actor:
    user_id: str
    role: str
    token: str


# init_db() nur 1x pro Prozess (FastAPI/Uvicorn Worker)
_DB_INIT_DONE = False


def _ensure_db_inited(db_path: str) -> None:
    global _DB_INIT_DONE
    if _DB_INIT_DONE:
        return
    init_db(db_path)
    _DB_INIT_DONE = True


def _parse_iso_dt(value: str) -> datetime:
    """
    Robust gegen 'Z' (UTC) und normale ISO Strings.
    """
    v = (value or "").strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    return datetime.fromisoformat(v)


def get_current_user(request: Request) -> Actor:
    settings = load_auth_settings()
    _ensure_db_inited(settings.db_path)

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="unauthorized")

    prefix = "bearer "
    if not auth.lower().startswith(prefix):
        raise HTTPException(status_code=401, detail="unauthorized")

    token = auth[len(prefix) :].strip()
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")

    h = token_hash_fn(settings.secret_key)(token)

    with db(settings.db_path) as conn:
        sess = get_session_by_token_hash(conn, h)
        if not sess:
            raise HTTPException(status_code=401, detail="unauthorized")

        expires_at = sess.get("expires_at")
        if not expires_at:
            raise HTTPException(status_code=401, detail="unauthorized")

        try:
            exp = _parse_iso_dt(str(expires_at))
        except Exception:
            raise HTTPException(status_code=401, detail="unauthorized")

        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="unauthorized")

        return Actor(
            user_id=str(sess["user_id"]),
            role=str(sess["role"]),
            token=token,
        )


def require_roles(*allowed: str) -> Callable[[Actor], Actor]:
    def _dep(actor: Actor = Depends(get_current_user)) -> Actor:
        if actor.role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return actor

    return _dep
