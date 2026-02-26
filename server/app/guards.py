from __future__ import annotations

from typing import Any, Iterable, Set

from fastapi import Depends, HTTPException

from app.rbac import get_current_user


def _norm_roles(roles: Iterable[str]) -> Set[str]:
    return {str(r).strip().lower() for r in roles if str(r).strip()}


def _user_role(user: Any) -> str:
    """
    Unterstützt:
    - None
    - dict (Actor TypedDict)
    - Objekt mit role/role_name/role_id Attribut
    """
    if user is None:
        return ""

    if isinstance(user, dict):
        role = user.get("role") or user.get("role_name") or user.get("role_id") or ""
        return str(role).strip().lower()

    role = getattr(user, "role", None) or getattr(user, "role_name", None) or getattr(user, "role_id", None) or ""
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
    # Moderator strikt nur Blog/News
    role = _user_role(current_user)
    if role == "moderator":
        raise HTTPException(status_code=403, detail="role_not_allowed")
    return current_user