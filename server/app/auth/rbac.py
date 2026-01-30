from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Set, Any, Iterator

from fastapi import Depends, Header, HTTPException, status

from .service import resolve_me
from .settings import AuthSettings, load_settings


def get_auth_settings() -> AuthSettings:
    # nutzt euren bestehenden Env-Loader (wirft bei zu kurzem Secret sauber Fehler)
    return load_settings()


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: str

    # --- Kompatibilität: tuple-unpacking + dict-like access ---
    def __iter__(self) -> Iterator[str]:
        yield self.user_id
        yield self.role

    def __getitem__(self, key: str) -> Any:
        if key == "user_id":
            return self.user_id
        if key == "role":
            return self.role
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    settings: AuthSettings = Depends(get_auth_settings),
) -> AuthContext:
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    me = resolve_me(settings, token)
    if me is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, role = me
    return AuthContext(user_id=user_id, role=role)


def require_roles(*allowed_roles: str) -> Callable[..., AuthContext]:
    """
    Deny-by-default RBAC Guard.
    - fehlender/ungültiger Token -> 401 (über get_current_user)
    - falsche Rolle -> 403
    """
    allowed: Set[str] = set(allowed_roles)

    def _dep(user: AuthContext = Depends(get_current_user)) -> AuthContext:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="forbidden",
            )
        return user

    return _dep
