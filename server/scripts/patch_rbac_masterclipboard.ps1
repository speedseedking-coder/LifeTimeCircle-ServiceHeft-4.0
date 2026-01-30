# Patch: Erzwingt RBAC serverseitig für Masterclipboard Router (deny-by-default)
# - Importiert Depends + require_roles
# - Fügt Router-level dependency hinzu: user|vip|dealer|admin (public + moderator block)
#
# Ausführen:
#   cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"
#   pwsh -ExecutionPolicy Bypass -File .\scripts\patch_rbac_masterclipboard.ps1
#   poetry run pytest

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$routerPath = Join-Path $serverRoot "app\routers\masterclipboard.py"

if (-not (Test-Path $routerPath)) {
  Write-Host "FEHLT: $routerPath"
  exit 1
}

function Backup-File([string]$path) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  Copy-Item $path "$path.bak.$ts" -Force
}

$raw = Get-Content -Path $routerPath -Raw -Encoding UTF8
$orig = $raw

# Skip wenn schon gepatcht
if ($raw -match 'require_roles\(') {
  Write-Host "OK: masterclipboard.py hat bereits require_roles(...)"
  exit 0
}

# 1) fastapi import: Depends ergänzen
# - from fastapi import APIRouter -> from fastapi import APIRouter, Depends
# - wenn bereits vorhanden: nichts tun
if ($raw -match '(?m)^\s*from\s+fastapi\s+import\s+.*\bDepends\b') {
  # ok
} elseif ($raw -match '(?m)^\s*from\s+fastapi\s+import\s+APIRouter\s*$') {
  $raw = [regex]::Replace($raw, '(?m)^\s*from\s+fastapi\s+import\s+APIRouter\s*$', 'from fastapi import APIRouter, Depends', 1)
} elseif ($raw -match '(?m)^\s*from\s+fastapi\s+import\s+([^\r\n]+)\s*$') {
  $raw = [regex]::Replace(
    $raw,
    '(?m)^\s*from\s+fastapi\s+import\s+([^\r\n]+)\s*$',
    {
      param($m)
      $imports = $m.Groups[1].Value.Trim()
      if ($imports -match '\bDepends\b') { return $m.Value }
      return "from fastapi import $imports, Depends"
    },
    1
  )
} else {
  # Fallback: ganz oben importieren
  $raw = "from fastapi import Depends`r`n" + $raw
}

# 2) require_roles Import ergänzen (nach den anderen app-imports)
if ($raw -notmatch '(?m)^\s*from\s+app\.auth\.rbac\s+import\s+require_roles\s*$') {
  if ($raw -match '(?m)^\s*from\s+app\.[^\r\n]+$') {
    $raw = [regex]::Replace(
      $raw,
      '(?m)(^\s*from\s+app\.[^\r\n]+$\r?\n)',
      '$1from app.auth.rbac import require_roles' + "`r`n",
      1
    )
  } else {
    # Fallback: nach fastapi imports
    $raw = [regex]::Replace(
      $raw,
      '(?m)(^\s*from\s+fastapi\s+import\s+[^\r\n]+$\r?\n)',
      '$1from app.auth.rbac import require_roles' + "`r`n",
      1
    )
  }
}

# 3) Router-level dependency hinzufügen
# router = APIRouter(  -> router = APIRouter(
#                        dependencies=[Depends(require_roles("user","vip","dealer","admin"))],
#                      ...
$depLine = "router = APIRouter(`r`n    dependencies=[Depends(require_roles(""user"",""vip"",""dealer"",""admin""))],`r`n"
if ($raw -match 'router\s*=\s*APIRouter\s*\(') {
  $raw = [regex]::Replace($raw, 'router\s*=\s*APIRouter\s*\(', $depLine, 1)
} else {
  Write-Host "FEHLT: Konnte 'router = APIRouter(' nicht finden."
  exit 2
}

if ($raw -ne $orig) {
  Backup-File $routerPath
  Set-Content -Path $routerPath -Value $raw -Encoding UTF8
  Write-Host "OK: RBAC Guard auf Masterclipboard Router gesetzt"
} else {
  Write-Host "OK: Keine Änderungen nötig"
}

Write-Host "FERTIG ✅"
