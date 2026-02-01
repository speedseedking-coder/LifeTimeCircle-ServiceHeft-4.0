# server/app/guards.py
from __future__ import annotations

from typing import Iterable, Set

from fastapi import Depends, HTTPException
from app.rbac import get_current_user
def _norm_roles(roles: Iterable[str]) -> Set[str]:
    return {str(r).strip().lower() for r in roles if str(r).strip()}


def _user_role(user: object) -> str:
    role = getattr(user, "role", None)
    if role is None:
        return ""
    return str(role).strip().lower()


def forbid_roles(*blocked_roles: str):
    blocked = _norm_roles(blocked_roles)

    def _dep(current_user=Depends(get_current_user)):
        role = _user_role(current_user)
        if role in blocked:
            raise HTTPException(status_code=403, detail="role_not_allowed")
        return current_user

    return _dep


def forbid_moderator(current_user=Depends(get_current_user)):
    role = _user_role(current_user)
    if role == "moderator":
        raise HTTPException(status_code=403, detail="role_not_allowed")
    return current_user
