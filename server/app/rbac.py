# server/app/rbac.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional, Set, TypedDict
import threading

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.settings import load_settings as load_auth_settings
from app.auth.service import db, token_hash_fn, get_session_by_token_hash, init_db


class Actor(TypedDict):
    user_id: str
    role: str
    token: str


# Compatibility-Alias (falls irgendwo "AuthContext" verwendet wird)
AuthContext = Actor

_bearer = HTTPBearer(auto_error=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# init_db nur einmal pro DB-Pfad
_db_inited: set[str] = set()
_db_lock = threading.Lock()


def _ensure_db_inited(db_path: str) -> None:
    if db_path in _db_inited:
        return
    with _db_lock:
        if db_path in _db_inited:
            return
        init_db(db_path)
        _db_inited.add(db_path)


def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[Actor]:
    """
    Liefert Actor (user_id/role/token) oder None, wenn kein/ungültiger Token vorhanden ist.
    """
    if creds is None or not creds.credentials:
        return None

    raw_token = creds.credentials
    settings = load_auth_settings()
    _ensure_db_inited(settings.db_path)

    th = token_hash_fn(settings.secret_key, raw_token)

    with db(settings.db_path) as conn:
        sess = get_session_by_token_hash(conn, th)
        if sess is None:
            return None

        # revoked-session blocken, falls Feld existiert
        try:
            if hasattr(sess, "keys") and "revoked_at" in sess.keys() and sess["revoked_at"] is not None:
                return None
        except Exception:
            # falls Row-Objekt sich anders verhält: lieber fail-closed
            return None

        try:
            exp = datetime.fromisoformat(sess["expires_at"])
        except Exception:
            return None

        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if _utc_now() > exp:
            return None

        user_id = sess["user_id"]
        user = conn.execute(
            "SELECT * FROM auth_users WHERE user_id = ? LIMIT 1;", (user_id,)
        ).fetchone()
        if user is None:
            return None

        return {"user_id": user_id, "role": user["role"], "token": raw_token}


# Alias, weil einige Router "get_actor" erwarten
get_actor = get_current_user


def require_roles(*roles: str) -> Callable[..., Actor]:
    allowed: Set[str] = set(roles)

    def _dep(user: Optional[Actor] = Depends(get_current_user)) -> Actor:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
        if user["role"] not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _dep

# Telemetry helper: set role without identity
# NOTE: ensure to call this where request is available


