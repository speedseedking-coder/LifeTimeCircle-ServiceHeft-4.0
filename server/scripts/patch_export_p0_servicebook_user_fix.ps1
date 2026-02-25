Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root

function Read-Utf8([string]$path) {
  return [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
}
function Write-Utf8NoBom([string]$path, [string]$text) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $enc)
}

function Ensure-Contains([string]$text, [string]$needle, [string]$err) {
  if ($text -notlike "*$needle*") { throw $err }
}

# ------------------------------------------------------------
# 1) Router: forbid_moderator als Dependency hinzufügen
# ------------------------------------------------------------

$svcPath = Join-Path $root "server/app/routers/export_servicebook.py"
$usrPath = Join-Path $root "server/app/routers/export_user.py"

$svc = Read-Utf8 $svcPath
$usr = Read-Utf8 $usrPath

# export_servicebook: import + router dependencies
if ($svc -notmatch "(?m)^from app\.guards import forbid_moderator\s*$") {
  Ensure-Contains $svc "from app.routers.export_vehicle import get_actor, get_db" "export_servicebook.py: erwarteter Import-Anchor nicht gefunden."
  $svc = $svc -replace "(?m)^(from app\.routers\.export_vehicle import get_actor, get_db\s*)$",
    "`$1`nfrom app.guards import forbid_moderator"
}

$svc = $svc -replace "(?m)^router\s*=\s*APIRouter\(\s*prefix=""\/export\/servicebook"",\s*tags=\[\s*""export""\s*\]\s*\)\s*$",
  "router = APIRouter(prefix=""/export/servicebook"", tags=[""export""], dependencies=[Depends(forbid_moderator)])"

# export_user: import + router dependencies
if ($usr -notmatch "(?m)^from app\.guards import forbid_moderator\s*$") {
  Ensure-Contains $usr "from app.routers.export_vehicle import get_actor, get_db" "export_user.py: erwarteter Import-Anchor nicht gefunden."
  $usr = $usr -replace "(?m)^(from app\.routers\.export_vehicle import get_actor, get_db\s*)$",
    "`$1`nfrom app.guards import forbid_moderator"
}

$usr = $usr -replace "(?m)^router\s*=\s*APIRouter\(\s*prefix=""\/export\/user"",\s*tags=\[\s*""export""\s*\]\s*\)\s*$",
  "router = APIRouter(prefix=""/export/user"", tags=[""export""], dependencies=[Depends(forbid_moderator)])"

Write-Utf8NoBom $svcPath $svc
Write-Utf8NoBom $usrPath $usr

# ------------------------------------------------------------
# 2) Test: created_at korrekt als datetime für DateTime-Spalte
# ------------------------------------------------------------

$testPath = Join-Path $root "server/tests/test_export_servicebook_p0.py"
$test = Read-Utf8 $testPath

# Import erweitern
if ($test -notmatch "DateTime as SA_DateTime") {
  $test = $test -replace "(?m)^from sqlalchemy import (MetaData, Table, insert, select, text, update)\s*$",
    "from sqlalchemy import DateTime as SA_DateTime, MetaData, Table, insert, select, text, update"
}

# created_at assignment fix
$pattern = '(?m)^\s*if "created_at" in tbl\.c:\s*\r?\n\s*values\["created_at"\]\s*=\s*datetime\.now\(timezone\.utc\)\.isoformat\(\)\s*$'
if ($test -notmatch $pattern) {
  # Wenn das exakte Muster nicht passt, fail-fast statt "halb" patchen
  throw "test_export_servicebook_p0.py: created_at Block nicht im erwarteten Format gefunden."
}

$replacement = @'
        if "created_at" in tbl.c:
            col = tbl.c.created_at
            now = datetime.now(timezone.utc)
            values["created_at"] = now if isinstance(getattr(col, "type", None), SA_DateTime) else now.isoformat()
'@

$test = [regex]::Replace($test, $pattern, $replacement)
Write-Utf8NoBom $testPath $test

Write-Host "OK: Export P0 Fix angewendet (forbid_moderator deps + DateTime insert fix)."
Write-Host "NEXT: pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1"