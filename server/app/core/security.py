from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings


@dataclass(frozen=True)
class Actor:
    subject_id: str
    role: str
    org_id: str


bearer = HTTPBearer(auto_error=False)


def _deny(status_code: int, msg: str) -> None:
    raise HTTPException(status_code=status_code, detail=msg)


def decode_token(token: str) -> Actor:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        _deny(401, "unauthorized")

    sub = payload.get("sub")
    role = payload.get("role")
    org_id = payload.get("org_id")

    if not sub or not role or not org_id:
        _deny(401, "unauthorized")

    return Actor(subject_id=str(sub), role=str(role), org_id=str(org_id))


# --- SESSION_TOKEN_FALLBACK_LTC ---
# Akzeptiert neben JWT (core.security) auch Auth-Session-Tokens (/auth/verify).
# Keine Tokens/PII loggen. org_id Fallback: user_id (single-tenant / own-scope).
def decode_session_token(token: str):
    try:
        from app.auth.settings import load_settings as _load_auth_settings
        from app.auth.service import resolve_me as _resolve_me
    except Exception:
        _deny(401, "unauthorized")

    try:
        auth_settings = _load_auth_settings()
        me = _resolve_me(auth_settings, token)
        if me is None:
            _deny(401, "unauthorized")

        # me kann tuple/list, dict oder Objekt sein – robust extrahieren
        user_id = None
        role = None

        if isinstance(me, (tuple, list)) and len(me) >= 2:
            user_id = me[0]
            role = me[1]
        elif isinstance(me, dict):
            user_id = me.get("user_id") or me.get("id") or me.get("uid")
            role = me.get("role")
        else:
            user_id = getattr(me, "user_id", None) or getattr(me, "id", None) or getattr(me, "uid", None)
            role = getattr(me, "role", None)

        if not user_id or not role:
            _deny(401, "unauthorized")

        # org_id: MVP fallback = user_id (Scope-Isolation pro Account)
        return Actor(subject_id=str(user_id), role=str(role), org_id=str(user_id))
    except HTTPException:
        raise
    except Exception:
        _deny(401, "unauthorized")
def get_current_actor(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
):
    if not creds:
        _deny(401, "unauthorized")

    token = getattr(creds, "credentials", None)
    if not token:
        _deny(401, "unauthorized")

    try:
        return decode_token(token)
    except HTTPException as e:
        # SESSION_TOKEN_FALLBACK_LTC
        if getattr(e, "status_code", None) != 401:
            raise
        return decode_session_token(token)
def require_roles(*allowed: str):
    allowed_set = set(allowed)

    def _dep(actor: Annotated[Actor, Depends(get_current_actor)]) -> Actor:
        if actor.role not in allowed_set:
            _deny(403, "forbidden")
        return actor

    return _dep


# Helper nur für Tests/Dev (nicht loggen, keine Secrets in Logs)
def create_token(sub: str, role: str, org_id: str) -> str:
    settings = get_settings()
    return jwt.encode({"sub": sub, "role": role, "org_id": org_id}, settings.secret_key, algorithm=settings.jwt_algorithm)
