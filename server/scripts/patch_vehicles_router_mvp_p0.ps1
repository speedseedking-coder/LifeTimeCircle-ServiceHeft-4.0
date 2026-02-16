# server/scripts/patch_vehicles_router_mvp_p0.ps1
# RUN (Repo-Root):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_vehicles_router_mvp_p0.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _AsText {
  param([AllowNull()][object]$Value)
  if ($null -eq $Value) { return "" }
  return [string]$Value
}

function Write-Utf8NoBomFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowNull()][object]$Content
  )
  $dir = Split-Path -Parent $Path
  if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

  $text = (_AsText $Content).Replace("`r`n","`n")
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $text, $utf8NoBom)
}

function Update-FileIfChanged {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowNull()][object]$NewContent
  )

  $old = ""
  if (Test-Path $Path) {
    $tmp = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    $old = (_AsText $tmp)
  }

  $newText = (_AsText $NewContent)

  if ($old.Replace("`r`n","`n") -eq $newText.Replace("`r`n","`n")) {
    Write-Host "OK: unchanged $Path"
    return
  }

  Write-Utf8NoBomFile -Path $Path -Content $newText
  Write-Host "OK: updated $Path"
}

function Find-FromImportLine {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Symbol
  )
  if (!(Test-Path $Path)) { return $null }
  $txt = (_AsText (Get-Content $Path -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")
  if (-not $txt) { return $null }

  $pattern = "(?m)^\s*from\s+[A-Za-z0-9_\.]+\s+import\s+.*\b$([regex]::Escape($Symbol))\b.*$"
  $m = [regex]::Match($txt, $pattern)
  if ($m.Success) { return $m.Value.Trim() }
  return $null
}

# --- Repo-Root check ---
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

if (!(Test-Path "server/app/main.py")) {
  throw "Expected server/app/main.py not found. Run from Repo-Root."
}

# --- derive imports from existing working router (consent.py) ---
$consentPath = "server/app/routers/consent.py"
$requireActorImport = Find-FromImportLine -Path $consentPath -Symbol "require_actor"
if (-not $requireActorImport) { $requireActorImport = "from app.auth.actor import require_actor" }

$forbidModeratorImport = Find-FromImportLine -Path $consentPath -Symbol "forbid_moderator"
if (-not $forbidModeratorImport) { $forbidModeratorImport = "from app.auth.rbac import forbid_moderator" }

$getDbImport = Find-FromImportLine -Path $consentPath -Symbol "get_db"
if (-not $getDbImport) { $getDbImport = "from app.db import get_db" }

# --- 1) vehicles router (MVP) ---
$vehiclesPy = @"
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Optional, Tuple, Type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

$requireActorImport
$forbidModeratorImport
$getDbImport


VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{11,17}$")  # excludes I,O,Q
ALLOWED_ROLES = {"user", "vip", "dealer", "admin", "superadmin"}


def _role_of(actor: Any) -> str:
    return (
        getattr(actor, "role", None)
        or getattr(actor, "role_name", None)
        or getattr(actor, "role_id", None)
        or ""
    )


def _actor_id(actor: Any) -> Any:
    return getattr(actor, "user_id", None) or getattr(actor, "id", None) or getattr(actor, "subject", None)


def _normalize_vin(vin: str) -> str:
    v = (vin or "").strip().upper().replace(" ", "")
    if not VIN_RE.match(v):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_vin_format",
        )
    return v


def _mask_vin(vin: str) -> str:
    if not vin:
        return ""
    if len(vin) <= 7:
        return vin[0:1] + "***" + vin[-1:]
    return f"{vin[:3]}***{vin[-4:]}"


def _get_vehicle_model() -> Type[Any]:
    candidates = [
        ("app.models.vehicle", "Vehicle"),
        ("app.models.vehicles", "Vehicle"),
        ("app.models.vehicle_model", "Vehicle"),
        ("app.models.vehicle_models", "Vehicle"),
    ]
    for mod, name in candidates:
        try:
            m = __import__(mod, fromlist=[name])
            return getattr(m, name)
        except Exception:
            continue
    raise RuntimeError("Vehicle model not found (expected app.models.*.Vehicle)")


def _get_servicebook_model() -> Optional[Type[Any]]:
    candidates = [
        ("app.models.servicebook", "Servicebook"),
        ("app.models.servicebook", "ServiceBook"),
        ("app.models.service_book", "Servicebook"),
        ("app.models.service_book", "ServiceBook"),
        ("app.models.servicebooks", "Servicebook"),
        ("app.models.servicebooks", "ServiceBook"),
    ]
    for mod, name in candidates:
        try:
            m = __import__(mod, fromlist=[name])
            return getattr(m, name)
        except Exception:
            continue
    return None


def _find_owner_col(Vehicle: Type[Any]) -> Tuple[Optional[str], Any]:
    for name in ("owner_user_id", "owner_id", "user_id", "created_by_user_id"):
        if hasattr(Vehicle, name):
            return name, getattr(Vehicle, name)
    return None, None


def _coerce_pk(pk: str) -> Any:
    if pk.isdigit():
        try:
            return int(pk)
        except Exception:
            return pk
    return pk


def _vehicle_pk(vehicle: Any) -> Any:
    return getattr(vehicle, "id", None) or getattr(vehicle, "vehicle_id", None) or getattr(vehicle, "uuid", None)


def _maybe(vehicle: Any, *names: str) -> Any:
    for n in names:
        if hasattr(vehicle, n):
            return getattr(vehicle, n)
    return None


def _columns(model: Type[Any]) -> dict[str, Any]:
    try:
        return {c.name: c for c in model.__table__.columns}  # type: ignore[attr-defined]
    except Exception:
        return {}


def _set_if_present(kwargs: dict[str, Any], cols: dict[str, Any], names: tuple[str, ...], value: Any) -> bool:
    for n in names:
        if n in cols:
            kwargs[n] = value
            return True
    return False


class VehicleCreateIn(BaseModel):
    vin: str = Field(..., min_length=11, max_length=17)
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1886, le=2100)
    nickname: Optional[str] = None


class VehicleOut(BaseModel):
    id: str
    vin_masked: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    nickname: Optional[str] = None
    servicebook_id: Optional[str] = None


router = APIRouter(prefix="/vehicles", tags=["vehicles"], dependencies=[Depends(forbid_moderator)])


def _enforce_role(actor: Any) -> str:
    role = _role_of(actor)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return role


def _ensure_servicebook_if_needed(db: Session, actor: Any, vehicle: Any) -> None:
    if not hasattr(vehicle, "servicebook_id"):
        return
    if getattr(vehicle, "servicebook_id", None):
        return

    Servicebook = _get_servicebook_model()
    if Servicebook is None:
        return

    sb_cols = _columns(Servicebook)
    sb_kwargs: dict[str, Any] = {}

    vid = _vehicle_pk(vehicle)
    _set_if_present(sb_kwargs, sb_cols, ("vehicle_id",), vid)
    _set_if_present(sb_kwargs, sb_cols, ("vehicle_uuid",), vid)

    aid = _actor_id(actor)
    _set_if_present(sb_kwargs, sb_cols, ("owner_user_id", "owner_id", "user_id", "created_by_user_id"), aid)

    if "created_at" in sb_cols and sb_cols["created_at"].default is None and sb_cols["created_at"].server_default is None:
        sb_kwargs["created_at"] = datetime.utcnow()

    sb = Servicebook(**sb_kwargs)
    db.add(sb)
    db.commit()
    db.refresh(sb)

    sbid = getattr(sb, "id", None) or getattr(sb, "servicebook_id", None)
    if sbid is not None:
        setattr(vehicle, "servicebook_id", sbid)
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)


def _to_out(vehicle: Any) -> VehicleOut:
    vid = _vehicle_pk(vehicle)
    vin = _maybe(vehicle, "vin", "vin_raw", "vin_full") or ""
    return VehicleOut(
        id=str(vid),
        vin_masked=_mask_vin(str(vin)),
        make=_maybe(vehicle, "make", "brand", "manufacturer"),
        model=_maybe(vehicle, "model", "model_name"),
        year=_maybe(vehicle, "year", "build_year", "model_year"),
        nickname=_maybe(vehicle, "nickname", "display_name", "name"),
        servicebook_id=str(_maybe(vehicle, "servicebook_id")) if _maybe(vehicle, "servicebook_id") is not None else None,
    )


@router.post("", response_model=VehicleOut)
@router.post("/", response_model=VehicleOut)
def create_vehicle(
    payload: VehicleCreateIn,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleOut:
    role = _enforce_role(actor)
    Vehicle = _get_vehicle_model()

    owner_name, owner_col = _find_owner_col(Vehicle)
    if owner_col is None:
        raise HTTPException(status_code=500, detail="vehicle_owner_field_missing")

    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    if role == "user":
        existing = db.query(Vehicle).filter(owner_col == aid).count()
        if existing >= 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="vehicle_limit_reached")

    vin = _normalize_vin(payload.vin)
    cols = _columns(Vehicle)
    kwargs: dict[str, Any] = {}

    if owner_name and owner_name in cols:
        kwargs[owner_name] = aid

    _set_if_present(kwargs, cols, ("vin", "vin_raw", "vin_full"), vin)
    public_id = uuid.uuid4().hex
    _set_if_present(kwargs, cols, ("public_id", "public_vehicle_id", "public_qr_id", "public_token"), public_id)

    if payload.make:
        _set_if_present(kwargs, cols, ("make", "brand", "manufacturer"), payload.make)
    if payload.model:
        _set_if_present(kwargs, cols, ("model", "model_name"), payload.model)
    if payload.year is not None:
        _set_if_present(kwargs, cols, ("year", "build_year", "model_year"), payload.year)
    if payload.nickname:
        _set_if_present(kwargs, cols, ("nickname", "display_name", "name"), payload.nickname)

    if "created_at" in cols and cols["created_at"].default is None and cols["created_at"].server_default is None:
        kwargs["created_at"] = datetime.utcnow()

    v = Vehicle(**kwargs)
    db.add(v)
    db.commit()
    db.refresh(v)

    _ensure_servicebook_if_needed(db, actor, v)
    return _to_out(v)


@router.get("", response_model=list[VehicleOut])
@router.get("/", response_model=list[VehicleOut])
def list_vehicles(
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> list[VehicleOut]:
    role = _enforce_role(actor)
    Vehicle = _get_vehicle_model()
    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    owner_name, owner_col = _find_owner_col(Vehicle)
    if owner_col is None:
        raise HTTPException(status_code=500, detail="vehicle_owner_field_missing")

    q = db.query(Vehicle)

    if role not in {"admin", "superadmin"}:
        q = q.filter(owner_col == aid)

    cols = _columns(Vehicle)
    if "created_at" in cols and hasattr(Vehicle, "created_at"):
        q = q.order_by(getattr(Vehicle, "created_at").desc())  # type: ignore[attr-defined]

    return [_to_out(v) for v in q.all()]


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    actor: Any = Depends(require_actor),
) -> VehicleOut:
    role = _enforce_role(actor)
    Vehicle = _get_vehicle_model()
    aid = _actor_id(actor)
    if aid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    pk = _coerce_pk(vehicle_id)

    v = None
    try:
        v = db.get(Vehicle, pk)  # type: ignore[attr-defined]
    except Exception:
        if hasattr(Vehicle, "id"):
            v = db.query(Vehicle).filter(getattr(Vehicle, "id") == pk).first()  # type: ignore[attr-defined]

    if v is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if role in {"admin", "superadmin"}:
        return _to_out(v)

    owner_name, _ = _find_owner_col(Vehicle)
    if owner_name and hasattr(v, owner_name):
        if getattr(v, owner_name) != aid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return _to_out(v)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
"@

# --- do NOT overwrite vehicles.py if it already exists with a /vehicles router (prevents clobbering consent gate etc.) ---
$vehPath = "server/app/routers/vehicles.py"
$vehExisting = ""
if (Test-Path $vehPath) {
  $vehExisting = (_AsText (Get-Content $vehPath -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")
}
if ($vehExisting -match 'APIRouter\s*\(\s*prefix\s*=\s*"/vehicles"' -or $vehExisting -match 'prefix="/vehicles"' -or $vehExisting -match 'prefix\s*=\s*"/vehicles"') {
  Write-Host "OK: skip overwrite $vehPath (already has /vehicles router)"
} else {
  Update-FileIfChanged -Path "server/app/routers/vehicles.py" -NewContent $vehiclesPy
}

# --- 2) Wire router in server/app/main.py ---
$mainPath = "server/app/main.py"
$mainNorm = (_AsText (Get-Content $mainPath -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")

$importLine = "from app.routers.vehicles import router as vehicles_router"
if ($mainNorm -notmatch [regex]::Escape($importLine)) {
  $lines = $mainNorm -split "`n"
  $insertAt = -1
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^\s*from\s+app\.routers\.' ) { $insertAt = $i }
  }
  if ($insertAt -ge 0) {
    $newLines = @()
    for ($i=0; $i -lt $lines.Length; $i++) {
      $newLines += $lines[$i]
      if ($i -eq $insertAt) { $newLines += $importLine }
    }
    $mainNorm = ($newLines -join "`n")
  } else {
    $mainNorm = $importLine + "`n" + $mainNorm
  }
}

$includeLine = "    app.include_router(vehicles_router)"
if ($mainNorm -notmatch [regex]::Escape($includeLine)) {
  $lines = $mainNorm -split "`n"
  $newLines = @()
  $inserted = $false
  foreach ($ln in $lines) {
    $newLines += $ln
    if (-not $inserted -and $ln -match '^\s*app\.include_router\(consent_router\)\s*$') {
      $newLines += $includeLine
      $inserted = $true
    }
  }
  if (-not $inserted) {
    $newLines = @()
    $inserted2 = $false
    foreach ($ln in ($mainNorm -split "`n")) {
      $newLines += $ln
      if (-not $inserted2 -and $ln -match '^\s*app\.include_router\(export_vehicle_router\)\s*$') {
        $newLines += $includeLine
        $inserted2 = $true
      }
    }
    if (-not $inserted2) { $newLines += $includeLine }
  }
  $mainNorm = ($newLines -join "`n")
}

Update-FileIfChanged -Path $mainPath -NewContent $mainNorm

# --- 3) Docs fix: moderator allowlist alignment (SoT D-002) ---
$rmPath = "docs/03_RIGHTS_MATRIX.md"
if (Test-Path $rmPath) {
  $rm = (_AsText (Get-Content $rmPath -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")
  $rm = [regex]::Replace($rm, "(?m)^Stand:\s*\*\*\d{4}-\d{2}-\d{2}\*\*\s*$", "Stand: **2026-02-08**")
  Update-FileIfChanged -Path $rmPath -NewContent $rm
} else {
  Write-Host "WARN: docs/03_RIGHTS_MATRIX.md not found (skipped)"
}

Write-Host "DONE: vehicles router + main wiring (+ stand update)."