from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.db.session import get_db  # re-export (für Router, die app.deps.get_db importieren)
from app.rbac import Actor, get_actor, get_current_user


def _enforce(user: Actor | None, allowed: set[str]) -> Actor:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    if user["role"] not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user


def require_user(user: Actor | None = Depends(get_current_user)) -> Actor:
    """
    "Normale" eingeloggte Nutzer: user/vip/dealer/admin/superadmin
    (moderator + public werden hier bewusst ausgeschlossen).
    """
    return _enforce(user, {"user", "vip", "dealer", "admin", "superadmin"})


def require_vip_or_dealer(user: Actor | None = Depends(get_current_user)) -> Actor:
    """
    Für Funktionen wie Verkauf/Übergabe-QR etc. (VIP/Dealer).
    """
    return _enforce(user, {"vip", "dealer"})


def require_dealer(user: Actor | None = Depends(get_current_user)) -> Actor:
    return _enforce(user, {"dealer", "admin", "superadmin"})


def require_moderator(user: Actor | None = Depends(get_current_user)) -> Actor:
    return _enforce(user, {"moderator", "admin", "superadmin"})


def require_admin(user: Actor | None = Depends(get_current_user)) -> Actor:
    return _enforce(user, {"admin", "superadmin"})
