from __future__ import annotations

from fastapi import Depends

from .rbac import AuthContext, get_current_user, require_roles


# Diese Datei dient als "Compatibility Layer":
# Falls Router/Module noch app.auth.deps.* importieren,
# bleibt alles stabil – aber mit sauberem RBAC-Verhalten.


def require_user(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    """
    "Normale" eingeloggte Nutzer: user/vip/dealer/admin
    (moderator + public werden hier bewusst ausgeschlossen).
    """
    return require_roles("user", "vip", "dealer", "admin", "superadmin")(user=user)  # type: ignore[arg-type]


def require_vip_or_dealer(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    """
    Für Funktionen wie Verkauf/Übergabe-QR etc. (VIP/Dealer).
    """
    return require_roles("vip", "dealer")(user=user)  # type: ignore[arg-type]


def require_dealer(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    return require_roles("dealer", "admin", "superadmin")(user=user)  # type: ignore[arg-type]


def require_moderator(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    return require_roles("moderator", "admin", "superadmin")(user=user)  # type: ignore[arg-type]


def require_admin(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    return require_roles("admin", "superadmin")(user=user)  # type: ignore[arg-type]  # type: ignore[arg-type]


def require_superadmin(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    return require_roles("superadmin")(user=user)  # type: ignore[arg-type]
