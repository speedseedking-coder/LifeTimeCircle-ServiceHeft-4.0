param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function RepoRoot {
  (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir -and !(Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Write-Rel([string]$Rel, [string]$Content) {
  $full = Join-Path (RepoRoot) $Rel
  Write-Utf8NoBom -Path $full -Content $Content
}

# Nur Actor-SoT Modul anlegen (keine Router überschreiben auf main!)
Write-Rel "server/app/auth/actor.py" @'
from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request


DEV_HEADERS_ENV = "LTC_ALLOW_DEV_HEADERS"


def dev_headers_enabled() -> bool:
    v = (os.getenv(DEV_HEADERS_ENV, "") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def actor_role(actor: Any) -> str:
    if actor is None:
        return ""
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return str(getattr(actor, "role", "") or "")


def actor_user_id(actor: Any) -> Optional[str]:
    if actor is None:
        return None
    if isinstance(actor, dict):
        v = actor.get("user_id") or actor.get("id")
        return str(v) if v else None
    v = getattr(actor, "user_id", None) or getattr(actor, "id", None)
    return str(v) if v else None


def _actor_from_state(request: Request) -> Any:
    return getattr(request.state, "actor", None) or request.scope.get("actor")


def _actor_from_dev_headers(request: Request) -> Any:
    role = request.headers.get("X-Role") or request.headers.get("x-role")
    user_id = request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    if not role or not user_id:
        return None
    return {"role": role, "user_id": user_id}


def require_actor(request: Request) -> Any:
    # Source-of-Truth: Auth/Middleware setzt request.state.actor
    actor = _actor_from_state(request)
    if actor is not None:
        return actor

    # DEV/TEST only: Header-Fallback (explizit per ENV freischalten)
    if dev_headers_enabled():
        actor = _actor_from_dev_headers(request)
        if actor is not None:
            return actor

    raise HTTPException(status_code=401, detail="unauthorized")


def forbid_moderator(actor: Any = Depends(require_actor)) -> None:
    # Moderator strikt nur Blog/News
    if actor_role(actor).lower() == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")
'@

Write-Host "OK: app/auth/actor.py geschrieben (Actor-SoT zentral, DEV-Headers gated)."