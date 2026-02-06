# server/scripts/patch_consent_p0_add_files_and_mount.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content.Replace("`r`n","`n"), $utf8NoBom)
}

function Ensure-LineInFile([string]$Path, [string]$Line) {
  if (-not (Test-Path $Path)) { return $false }
  $s = Get-Content -Raw -Path $Path
  if ($s -match [regex]::Escape($Line)) { return $true }
  $s2 = $s.TrimEnd() + "`n" + $Line + "`n"
  Write-FileUtf8NoBom -Path $Path -Content $s2
  return $true
}

function Patch-MainMountConsent([string]$MainPath) {
  if (-not (Test-Path $MainPath)) { throw "FEHLT: $MainPath" }
  $src = Get-Content -Raw -Path $MainPath

  $importLine = "from app.routers.consent import router as consent_router"
  $includeLine = "app.include_router(consent_router)"

  $changed = $false

  if ($src -notmatch [regex]::Escape($importLine)) {
    # Insert after last "from app.routers." import if possible, else after import block, else at top.
    $m = [regex]::Match($src, "(?ms)^(from\s+app\.routers\..*\r?\n)+(?!from\s+app\.routers\.)")
    if ($m.Success) {
      $idx = $m.Index + $m.Length
      $src = $src.Insert($idx, $importLine + "`n")
    } else {
      $m2 = [regex]::Match($src, "(?ms)^(import .*?\r?\n|from .*? import .*?\r?\n)+")
      if ($m2.Success) {
        $idx = $m2.Index + $m2.Length
        $src = $src.Insert($idx, $importLine + "`n")
      } else {
        $src = $importLine + "`n" + $src
      }
    }
    $changed = $true
  }

  if ($src -notmatch [regex]::Escape($includeLine)) {
    # Prefer: after export_router include if present, else after last include_router.
    if ($src -match "(?m)^\s*app\.include_router\(export_router\)\s*$") {
      $src = [regex]::Replace(
        $src,
        "(?m)^\s*app\.include_router\(export_router\)\s*$",
        "app.include_router(export_router)`napp.include_router(consent_router)",
        1
      )
    } elseif ($src -match "(?ms)app\.include_router\(") {
      $src = [regex]::Replace(
        $src,
        "(?ms)(.*app\.include_router\([^\)]*\).*\r?\n)(?!.*app\.include_router\()",
        "`$1$includeLine`n",
        1
      )
    } else {
      $src = $src.TrimEnd() + "`n`n" + $includeLine + "`n"
    }
    $changed = $true
  }

  if ($changed) {
    Copy-Item $MainPath "$MainPath.bak" -Force
    Write-FileUtf8NoBom -Path $MainPath -Content $src
    return $true
  }
  return $false
}

# --- Locate server root (script is in server/scripts) ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverRoot = Split-Path -Parent $scriptDir

$consentPolicyPath = Join-Path $serverRoot "app\consent\policy.py"
$consentModelPath  = Join-Path $serverRoot "app\models\consent.py"
$consentStorePath  = Join-Path $serverRoot "app\services\consent_store.py"
$consentRouterPath = Join-Path $serverRoot "app\routers\consent.py"
$testPath          = Join-Path $serverRoot "tests\test_consent_contract.py"

$mainPath          = Join-Path $serverRoot "app\main.py"
$dbBasePath        = Join-Path $serverRoot "app\db\base.py"

Write-Host "ServerRoot: $serverRoot"

# 1) policy.py
if (-not (Test-Path $consentPolicyPath)) {
  Write-FileUtf8NoBom $consentPolicyPath @'
from __future__ import annotations

from typing import Final

DOC_TERMS: Final[str] = "terms"
DOC_PRIVACY: Final[str] = "privacy"

SOURCE_UI: Final[str] = "ui"
SOURCE_API: Final[str] = "api"

# Single Source of Truth: required consent documents and their current versions.
CURRENT_DOC_VERSIONS: Final[dict[str, str]] = {
    DOC_TERMS: "v1",
    DOC_PRIVACY: "v1",
}

ALLOWED_DOC_TYPES: Final[frozenset[str]] = frozenset(CURRENT_DOC_VERSIONS.keys())
ALLOWED_SOURCES: Final[frozenset[str]] = frozenset({SOURCE_UI, SOURCE_API})


def required_consents() -> list[dict[str, str]]:
    return [{"doc_type": dt, "doc_version": ver} for dt, ver in CURRENT_DOC_VERSIONS.items()]
'@
  Write-Host "OK: angelegt $consentPolicyPath"
} else {
  Write-Host "OK: existiert $consentPolicyPath"
}

# 2) models/consent.py
if (-not (Test-Path $consentModelPath)) {
  Write-FileUtf8NoBom $consentModelPath @'
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsentAcceptance(Base):
    __tablename__ = "consent_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # UUID stored as string (SQLite-friendly)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    doc_version: Mapped[str] = mapped_column(String(32), nullable=False)

    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Contract: source ∈ {ui, api}
    source: Mapped[str] = mapped_column(String(16), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "doc_type", "doc_version", name="uq_consent_user_doc_ver"),
        Index("ix_consent_user_doc_type", "user_id", "doc_type"),
    )
'@
  Write-Host "OK: angelegt $consentModelPath"
} else {
  Write-Host "OK: existiert $consentModelPath"
}

# 3) services/consent_store.py
if (-not (Test-Path $consentStorePath)) {
  Write-FileUtf8NoBom $consentStorePath @'
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consent.policy import (
    ALLOWED_DOC_TYPES,
    ALLOWED_SOURCES,
    CURRENT_DOC_VERSIONS,
    required_consents,
)
from app.models.consent import ConsentAcceptance


class ConsentContractError(ValueError):
    pass


def _parse_iso8601_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ConsentContractError("accepted_at muss ISO8601 string sein")

    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception as e:
        raise ConsentContractError("accepted_at ist kein gültiger ISO8601 Zeitstempel") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_and_normalize_consents(consents: Any) -> list[dict[str, Any]]:
    if consents is None:
        return []
    if not isinstance(consents, list):
        raise ConsentContractError("consents muss eine Liste sein")

    out: list[dict[str, Any]] = []
    seen_types: set[str] = set()

    for i, item in enumerate(consents):
        if not isinstance(item, dict):
            raise ConsentContractError(f"consents[{i}] muss ein Objekt sein")

        doc_type = item.get("doc_type")
        doc_version = item.get("doc_version")
        accepted_at = item.get("accepted_at")
        source = item.get("source")

        if doc_type not in ALLOWED_DOC_TYPES:
            raise ConsentContractError(f"consents[{i}].doc_type ungültig")
        if not isinstance(doc_version, str) or not doc_version.strip():
            raise ConsentContractError(f"consents[{i}].doc_version fehlt")
        if source not in ALLOWED_SOURCES:
            raise ConsentContractError(f"consents[{i}].source muss ui oder api sein")
        if accepted_at is None:
            raise ConsentContractError(f"consents[{i}].accepted_at fehlt")

        dt = _parse_iso8601_utc(str(accepted_at))

        if doc_type in seen_types:
            raise ConsentContractError(f"doc_type doppelt: {doc_type}")
        seen_types.add(doc_type)

        out.append(
            {
                "doc_type": doc_type,
                "doc_version": doc_version.strip(),
                "accepted_at": dt,
                "source": source,
            }
        )

    return out


def ensure_required_consents(normalized: list[dict[str, Any]]) -> None:
    by_type = {c["doc_type"]: c for c in normalized}
    missing: list[str] = []

    for doc_type, required_ver in CURRENT_DOC_VERSIONS.items():
        got = by_type.get(doc_type)
        if got is None or got.get("doc_version") != required_ver:
            missing.append(f"{doc_type}:{required_ver}")

    if missing:
        raise ConsentContractError("Pflicht-Consents fehlen oder Version falsch: " + ", ".join(missing))


def record_consents(db: Session, user_id: str, normalized: list[dict[str, Any]]) -> None:
    now = datetime.now(tz=timezone.utc)

    for c in normalized:
        stmt = select(ConsentAcceptance).where(
            ConsentAcceptance.user_id == user_id,
            ConsentAcceptance.doc_type == c["doc_type"],
            ConsentAcceptance.doc_version == c["doc_version"],
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            continue

        db.add(
            ConsentAcceptance(
                user_id=user_id,
                doc_type=c["doc_type"],
                doc_version=c["doc_version"],
                accepted_at=c["accepted_at"],
                source=c["source"],
                created_at=now,
            )
        )

    db.commit()


def get_user_consents(db: Session, user_id: str) -> list[dict[str, Any]]:
    stmt = select(ConsentAcceptance).where(ConsentAcceptance.user_id == user_id)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "doc_type": r.doc_type,
            "doc_version": r.doc_version,
            "accepted_at": r.accepted_at.astimezone(timezone.utc).isoformat(),
            "source": r.source,
        }
        for r in rows
    ]


def has_required_consents(db: Session, user_id: str) -> bool:
    rows = get_user_consents(db, user_id)
    have = {(r["doc_type"], r["doc_version"]) for r in rows}
    for doc_type, ver in CURRENT_DOC_VERSIONS.items():
        if (doc_type, ver) not in have:
            return False
    return True
'@
  Write-Host "OK: angelegt $consentStorePath"
} else {
  Write-Host "OK: existiert $consentStorePath"
}

# 4) routers/consent.py
if (-not (Test-Path $consentRouterPath)) {
  Write-FileUtf8NoBom $consentRouterPath @'
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.consent.policy import required_consents
from app.deps import get_db
from app.guards import forbid_moderator
from app.rbac import get_current_user
from app.services.consent_store import (
    ConsentContractError,
    ensure_required_consents,
    get_user_consents,
    record_consents,
    validate_and_normalize_consents,
)

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentItem(BaseModel):
    doc_type: str
    doc_version: str
    accepted_at: str
    source: str


class ConsentAcceptRequest(BaseModel):
    consents: list[ConsentItem] = Field(default_factory=list)


def _dump_model(m: BaseModel) -> dict[str, Any]:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()


@router.get("/current")
def consent_current():
    # public discovery endpoint (no auth)
    return {"required": required_consents()}


@router.get("/status", dependencies=[Depends(forbid_moderator)])
def consent_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    accepted = get_user_consents(db, str(user.id))
    required = required_consents()
    have = {(a["doc_type"], a["doc_version"]) for a in accepted}
    is_complete = all((r["doc_type"], r["doc_version"]) in have for r in required)
    return {"required": required, "accepted": accepted, "is_complete": is_complete}


@router.post("/accept", dependencies=[Depends(forbid_moderator)])
def consent_accept(payload: ConsentAcceptRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        raw = [_dump_model(x) for x in payload.consents]
        normalized = validate_and_normalize_consents(raw)
        ensure_required_consents(normalized)
        record_consents(db, str(user.id), normalized)
        return {"ok": True}
    except ConsentContractError as e:
        raise HTTPException(status_code=400, detail=str(e))
'@
  Write-Host "OK: angelegt $consentRouterPath"
} else {
  Write-Host "OK: existiert $consentRouterPath"
}

# 5) tests
if (-not (Test-Path $testPath)) {
  Write-FileUtf8NoBom $testPath @'
from __future__ import annotations

import pytest

from app.services.consent_store import (
    ConsentContractError,
    ensure_required_consents,
    validate_and_normalize_consents,
)


def test_rejects_source_web():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "web"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    with pytest.raises(ConsentContractError):
        validate_and_normalize_consents(consents)


def test_requires_accepted_at():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    with pytest.raises(ConsentContractError):
        validate_and_normalize_consents(consents)


def test_requires_exact_current_versions():
    consents = [
        {"doc_type": "terms", "doc_version": "v2", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
    ]
    normalized = validate_and_normalize_consents(consents)
    with pytest.raises(ConsentContractError):
        ensure_required_consents(normalized)


def test_accepts_valid_set():
    consents = [
        {"doc_type": "terms", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "ui"},
        {"doc_type": "privacy", "doc_version": "v1", "accepted_at": "2026-02-01T00:00:00Z", "source": "api"},
    ]
    normalized = validate_and_normalize_consents(consents)
    ensure_required_consents(normalized)
'@
  Write-Host "OK: angelegt $testPath"
} else {
  Write-Host "OK: existiert $testPath"
}

# 6) DB model registration (optional but recommended)
$importModelLine = "from app.models.consent import ConsentAcceptance  # noqa: F401"
if (Test-Path $dbBasePath) {
  $ok = Ensure-LineInFile -Path $dbBasePath -Line $importModelLine
  if ($ok) { Write-Host "OK: db/base.py importiert ConsentAcceptance (oder ergänzt)" }
} else {
  Write-Warning "HINWEIS: app/db/base.py nicht gefunden ($dbBasePath). Falls Tabellen fehlen: Model-Import dort ergänzen."
}

# 7) Mount router in main.py
$patched = Patch-MainMountConsent -MainPath $mainPath
if ($patched) {
  Write-Host "OK: app/main.py gepatcht (consent_router import + include). Backup: $mainPath.bak"
} else {
  Write-Host "OK: app/main.py war bereits ok (kein Patch nötig)"
}

Write-Host "DONE"
