# server/scripts/patch_register_documents_router.ps1
param(
  [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  param([string]$Root)
  if ($Root -and (Test-Path -LiteralPath $Root)) {
    return (Resolve-Path -LiteralPath $Root).Path
  }
  # script: server/scripts -> repo root = ../..
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

$repo = Resolve-RepoRoot $RepoRoot
$mainPy = Join-Path $repo "server\app\main.py"

if (-not (Test-Path -LiteralPath $mainPy)) {
  Write-Host "ERROR: main.py nicht gefunden: $mainPy"
  exit 1
}

$content = Get-Content -LiteralPath $mainPy -Raw -Encoding UTF8
if ($content -match "documents\.router") {
  Write-Host "OK: documents.router ist bereits registriert in server/app/main.py"
  exit 0
}

$lines = Get-Content -LiteralPath $mainPy -Encoding UTF8

# --- Import einfügen ---
$hasImportLine = $false
foreach ($l in $lines) {
  if ($l -match "^\s*from\s+app\.routers\s+import\s+.*\bdocuments\b") {
    $hasImportLine = $true
    break
  }
}
if (-not $hasImportLine) {
  $routerImportIdx = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^\s*from\s+app\.routers\s+import\s+") {
      $routerImportIdx += $i
    }
  }

  if ($routerImportIdx.Count -gt 0) {
    $insertAt = $routerImportIdx[-1] + 1
    $lines = $lines[0..($insertAt-1)] + @("from app.routers import documents") + $lines[$insertAt..($lines.Count-1)]
    Write-Host "OK: Import eingefügt nach letzter 'from app.routers import ...' Zeile."
  } else {
    # fallback: nach letztem allgemeinen import-block am Dateianfang
    $lastImport = -1
    for ($i=0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match "^\s*(from|import)\s+") { $lastImport = $i } else { break }
    }
    $insertAt = $lastImport + 1
    if ($insertAt -lt 0) { $insertAt = 0 }
    $lines = $lines[0..($insertAt-1)] + @("from app.routers import documents") + $lines[$insertAt..($lines.Count-1)]
    Write-Host "OK: Import eingefügt nach generischem Import-Block."
  }
}

# --- include_router einfügen ---
$includeIdx = @()
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match "app\.include_router\s*\(") {
    $includeIdx += $i
  }
}

if ($includeIdx.Count -gt 0) {
  $insertAt = $includeIdx[-1] + 1
  $lines = $lines[0..($insertAt-1)] + @("app.include_router(documents.router)") + $lines[$insertAt..($lines.Count-1)]
  Write-Host "OK: app.include_router(documents.router) eingefügt nach letztem include_router."
} else {
  # fallback: nach App-Erstellung
  $appIdx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^\s*app\s*=\s*FastAPI\s*\(" -or $lines[$i] -match "^\s*app\s*=\s*FastAPI\s*\(\s*\)\s*$") {
      $appIdx = $i
      break
    }
  }
  if ($appIdx -lt 0) {
    Write-Host "ERROR: Konnte keine App-Erstellung (app = FastAPI(...)) finden. Bitte main.py manuell patchen."
    exit 2
  }
  $insertAt = $appIdx + 1
  $lines = $lines[0..($insertAt-1)] + @("app.include_router(documents.router)") + $lines[$insertAt..($lines.Count-1)]
  Write-Host "OK: app.include_router(documents.router) eingefügt nach app = FastAPI(...)."
}

Set-Content -LiteralPath $mainPy -Value $lines -Encoding UTF8
Write-Host "DONE: server/app/main.py gepatcht."