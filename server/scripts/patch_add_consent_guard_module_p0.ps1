# server/scripts/patch_add_consent_guard_module_p0.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $dir = Get-Location
  for ($i = 0; $i -lt 12; $i++) {
    if (Test-Path (Join-Path $dir ".git")) { return (Resolve-Path $dir).Path }
    $parent = Split-Path -Parent $dir
    if ($parent -eq $dir) { break }
    $dir = $parent
  }
  throw "Repo-Root nicht gefunden (.git). Bitte im Repo-Root ausführen."
}

function Write-Utf8NoBom([string]$path, [string]$content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
}

$root = Resolve-RepoRoot

$consentDir = Join-Path $root "server/app/consent"
$initPy     = Join-Path $consentDir "__init__.py"
$guardPy    = Join-Path $consentDir "guard.py"
$vehPath    = Join-Path $root "server/app/routers/vehicles.py"

if (!(Test-Path $vehPath)) { throw "Nicht gefunden: $vehPath" }
if (!(Test-Path $consentDir)) { New-Item -ItemType Directory -Force -Path $consentDir | Out-Null }
if (!(Test-Path $initPy)) { Write-Utf8NoBom $initPy "# consent package`n" }

if (!(Test-Path $guardPy)) {
  $guard = @'
# server/app/consent/guard.py
from __future__ import annotations

import importlib
import inspect
from typing import Any, Optional

from fastapi import Depends, HTTPException

# project-safe db/actor deps (in diesem Repo existiert export_vehicle sicher)
from app.routers.export_vehicle import get_db, get_actor  # type: ignore


def _actor_get(actor: Any, key: str) -> Any:
    if actor is None:
        return None
    if isinstance(actor, dict):
        return actor.get(key)
    return getattr(actor, key, None)


def _extract_bool(maybe: Any) -> Optional[bool]:
    if isinstance(maybe, bool):
        return maybe
    return None


def _status_accepted(status: Any) -> Optional[bool]:
    """
    Erwartet bei /consent/status typischerweise accepted/is_accepted o.ä.
    """
    if isinstance(status, dict):
        for k in ("accepted", "is_accepted", "consent_accepted"):
            v = _extract_bool(status.get(k))
            if v is not None:
                return v
        # negatives Signal priorisieren
        for k in ("needs_reconsent", "reconsent_required", "consent_required"):
            v = _extract_bool(status.get(k))
            if v is True:
                return False
    return None


async def _call_status_fn(fn: Any, *, db: Any, actor: Any) -> Any:
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    for name, p in sig.parameters.items():
        if name in ("db", "session"):
            kwargs[name] = db
        elif name in ("actor", "current_actor", "user"):
            kwargs[name] = actor
        elif name in ("user_id", "uid"):
            uid = _actor_get(actor, "user_id") or _actor_get(actor, "id")
            kwargs[name] = uid
        else:
            # unknown param -> nur wenn default vorhanden, sonst skip (TypeError)
            if p.default is inspect._empty:
                raise TypeError("unsupported_signature")
    out = fn(**kwargs)
    if inspect.isawaitable(out):
        return await out
    return out


async def _get_consent_status(*, db: Any, actor: Any) -> Any:
    """
    Robust: versucht in typischen Consent-Modulen eine Status-Funktion zu finden.
    deny-by-default: wenn nichts gefunden/interpretierbar -> 403 consent_required
    """
    candidates = [
        ("app.routers.consent", ("consent_status", "get_status", "status")),
        ("app.consent.service", ("consent_status", "get_status", "get_consent_status", "status")),
        ("app.consent", ("consent_status", "get_status", "get_consent_status", "status")),
    ]

    last_exc: Optional[Exception] = None
    for mod_name, fn_names in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:  # pragma: no cover
            last_exc = e
            continue

        for fn_name in fn_names:
            fn = getattr(mod, fn_name, None)
            if not callable(fn):
                continue
            try:
                return await _call_status_fn(fn, db=db, actor=actor)
            except HTTPException:
                raise
            except Exception as e:  # pragma: no cover
                last_exc = e
                continue

    if last_exc:
        # kein Leak: keine Details nach außen
        pass
    raise HTTPException(status_code=403, detail="consent_required")


async def require_consent(db: Any = Depends(get_db), actor: Any = Depends(get_actor)) -> None:
    status = await _get_consent_status(db=db, actor=actor)
    accepted = _status_accepted(status)

    # deny-by-default
    if accepted is True:
        return

    # falls Status-Objekt nicht interpretierbar ist: ebenfalls deny
    raise HTTPException(status_code=403, detail="consent_required")
'@
  Write-Utf8NoBom $guardPy $guard
}

# vehicles.py: require_consent-Block auf neuen Guard normalisieren (idempotent)
$veh = Get-Content -Raw -Encoding UTF8 $vehPath
$veh2 = $veh

# Ersetze alten try/except (auth.consent -> consent.guard) durch single import
$pattern = '(?s)try:\s*\n\s*from app\.auth\.consent import require_consent[^\n]*\nexcept Exception[^\n]*\n\s*from app\.consent\.guard import require_consent[^\n]*\n'
$replacement = "from app.consent.guard import require_consent  # type: ignore`n"
$veh2 = [System.Text.RegularExpressions.Regex]::Replace($veh2, $pattern, $replacement)

# Falls noch ein anderes require_consent-import drinsteht: nicht anfassen.
if (-not ($veh2.EndsWith("`n") -or $veh2.EndsWith("`r`n"))) { $veh2 += "`n" }

if ($veh2 -ne $veh) { Write-Utf8NoBom $vehPath $veh2 }

Write-Host "OK: app.consent.guard created (deny-by-default) + vehicles.py import normalized."