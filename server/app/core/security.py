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


def get_current_actor(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> Actor:
    # deny-by-default: ohne Token -> 401
    if creds is None or not creds.credentials:
        _deny(401, "unauthorized")
    return decode_token(creds.credentials)


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
