# server/scripts/patch_moderator_missing_routes.ps1
<#
Fix P1: fehlende deny-Routen mit forbid_moderator absichern:
- /health (app.main @app.get)
- /admin/users* (via include_router prefix oder Router-Datei mit /admin/users)

Wichtig:
- Keine Änderungen an auth.py, public_qr.py, blog.py, news.py
- BOM-safe (UTF-8 mit/ohne BOM)
#>

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appDir     = Join-Path $serverRoot "app"
$routerDir  = Join-Path $appDir "routers"
$mainPath   = Join-Path $appDir "main.py"

if (-not (Test-Path $mainPath)) { throw "app/main.py nicht gefunden: $mainPath" }
if (-not (Test-Path $routerDir)) { throw "app/routers nicht gefunden: $routerDir" }

$SKIP = @("auth.py","public_qr.py","news.py","blog.py")

function Read-Utf8PreserveBom([string]$path) {
  $bytes = [System.IO.File]::ReadAllBytes($path)
  $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  $start = if ($hasBom) { 3 } else { 0 }
  $text = [System.Text.Encoding]::UTF8.GetString($bytes, $start, $bytes.Length - $start)
  return @{ text = $text; hasBom = $hasBom }
}

function Write-Utf8PreserveBom([string]$path, [string]$text, [bool]$hasBom) {
  $enc = New-Object System.Text.UTF8Encoding($hasBom)
  [System.IO.File]::WriteAllText($path, $text, $enc)
}

function Split-Lines([string]$text) {
  return [regex]::Split($text, "\r?\n")
}

function Join-Lines([string[]]$lines) {
  return ($lines -join "`n")
}

function Find-LastFutureIndex([string[]]$lines) {
  $last = -1
  for ($i=0; $i -lt [Math]::Min(120, $lines.Length); $i++) {
    if ($lines[$i].TrimStart() -match '^from\s+__future__\s+import\s+') { $last = $i }
  }
  return $last
}

function Ensure-ImportLineAfterFuture([string[]]$lines, [string]$importLine) {
  foreach ($ln in $lines) {
    if ($ln.Trim() -eq $importLine) { return $lines }
  }

  $lastFuture = Find-LastFutureIndex $lines
  $insertAt = if ($lastFuture -ge 0) { $lastFuture + 1 } else { 0 }

  $out = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($i -eq $insertAt) { $out.Add($importLine) | Out-Null }
    $out.Add($lines[$i]) | Out-Null
  }
  if ($insertAt -ge $lines.Length) { $out.Add($importLine) | Out-Null }
  return $out.ToArray()
}

function Ensure-DependsImported([string[]]$lines) {
  # already has Depends in "from fastapi import ..."
  foreach ($ln in $lines) {
    if ($ln -match '^\s*from\s+fastapi\s+import\s+.*\bDepends\b') { return $lines }
  }

  # extend first from fastapi import ...
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^\s*from\s+fastapi\s+import\s+(?<rest>.+)$') {
      if ($lines[$i] -notmatch '\bDepends\b') {
        $lines[$i] = $lines[$i].TrimEnd() + ", Depends"
      }
      return $lines
    }
  }

  # otherwise add "from fastapi import Depends" after future
  return (Ensure-ImportLineAfterFuture $lines "from fastapi import Depends")
}

function Patch-MainPy([string]$path) {
  $read = Read-Utf8PreserveBom $path
  $orig = [string]$read.text
  $hasBom = [bool]$read.hasBom

  $lines = Split-Lines $orig

  # Imports sicherstellen
  $lines = Ensure-ImportLineAfterFuture $lines "from app.guards import forbid_moderator"
  $lines = Ensure-DependsImported $lines

  # /health Decorator patchen (nur Single-Line)
  for ($i=0; $i -lt $lines.Length; $i++) {
    $ln = $lines[$i]
    if ($ln -match '^\s*@app\.get\(' -and $ln -match '["'']\/health\/?["'']') {
      if ($ln -match 'dependencies\s*=') { continue }
      if ($ln -match 'forbid_moderator') { continue }
      if ($ln.Contains(")")) {
        $lines[$i] = $ln -replace '\)\s*$', ', dependencies=[Depends(forbid_moderator)])'
      }
    }
  }

  # include_router(prefix="/admin/users...") patchen (nur wenn dependencies fehlt)
  for ($i=0; $i -lt $lines.Length; $i++) {
    $ln = $lines[$i]
    if ($ln -match 'app\.include_router\(' -and $ln -match 'prefix\s*=\s*["'']\/admin\/users') {
      if ($ln -match 'dependencies\s*=') { continue }
      if ($ln.Contains(")")) {
        $lines[$i] = $ln -replace '\)\s*$', ', dependencies=[Depends(forbid_moderator)])'
      }
    }
  }

  $newText = Join-Lines $lines
  if ($newText -ne $orig) {
    Write-Utf8PreserveBom $path $newText $hasBom
    Ok "main.py gepatcht: $path"
    return $true
  }

  Warn "main.py: keine Änderungen nötig"
  return $false
}

function Patch-AdminUsersRouterFiles([string]$dir) {
  $files = Get-ChildItem -Path $dir -Recurse -Filter "*.py"
  $changed = New-Object System.Collections.Generic.List[string]

  foreach ($f in $files) {
    if ($SKIP -contains $f.Name.ToLowerInvariant()) { continue }

    $path = $f.FullName
    $read = Read-Utf8PreserveBom $path
    $orig = [string]$read.text
    $hasBom = [bool]$read.hasBom

    # Nur wenn die Datei /admin/users wirklich enthält
    if ($orig -notmatch '["'']\/admin\/users') { continue }

    $lines = Split-Lines $orig

    # Imports sicherstellen
    $lines = Ensure-ImportLineAfterFuture $lines "from app.guards import forbid_moderator"
    $lines = Ensure-DependsImported $lines

    # router = APIRouter(...): dependencies einfügen (erste passende Zuweisung)
    $done = $false
    for ($i=0; $i -lt $lines.Length; $i++) {
      if ($lines[$i] -match '^\s*\w+\s*=\s*APIRouter\(') {
        if ($lines[$i] -match 'dependencies\s*=') { $done = $true; break }
        # inject direkt nach APIRouter(
        $lines[$i] = $lines[$i] -replace 'APIRouter\(', 'APIRouter(dependencies=[Depends(forbid_moderator)], '
        $done = $true
        break
      }
    }

    # Falls keine APIRouter-Zuweisung gefunden: nichts tun (bewusst)
    if (-not $done) { continue }

    $newText = Join-Lines $lines
    if ($newText -ne $orig) {
      Write-Utf8PreserveBom $path $newText $hasBom
      $changed.Add($path) | Out-Null
    }
  }

  if ($changed.Count -gt 0) {
    Ok "Admin-Users Router-Dateien gepatcht:"
    $changed | ForEach-Object { Write-Host " - $_" }
  } else {
    Warn "Keine Router-Datei mit '/admin/users' gefunden/geändert (dann kommt es nur über include_router-prefix)."
  }
}

# --- RUN ---
Patch-MainPy $mainPath | Out-Null
Patch-AdminUsersRouterFiles $routerDir

Ok "FERTIG ✅"
