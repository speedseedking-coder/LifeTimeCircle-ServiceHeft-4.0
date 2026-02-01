<#
P1 Fix: Moderator darf NICHT auf /admin/users*.
Wir patchen die Admin-Users Router-Datei (app/admin/**), nicht app/routers/**.

Logik:
- Suche unter app/admin nach Dateien, die APIRouter(prefix="/users") definieren
  ODER (Fallback) Routen-Strings "/users/{user_id}/role" oder "/users/{user_id}/moderator" enthalten.
- Für passende Datei:
  - import: from app.guards import forbid_moderator (nach __future__)
  - ensure Depends import (in "from fastapi import ..." ergänzen oder eigene Zeile)
  - router = APIRouter(...): dependencies=[Depends(forbid_moderator)] hinzufügen (wenn fehlt)
BOM-safe UTF-8.
#>

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$adminDir   = Join-Path $serverRoot "app\admin"
if (-not (Test-Path $adminDir)) { throw "app/admin nicht gefunden: $adminDir" }

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

function Split-Lines([string]$text) { return [regex]::Split($text, "\r?\n") }
function Join-Lines([string[]]$lines) { return ($lines -join "`n") }

function Find-LastFutureIndex([string[]]$lines) {
  $last = -1
  for ($i=0; $i -lt [Math]::Min(200, $lines.Length); $i++) {
    if ($lines[$i].TrimStart() -match '^from\s+__future__\s+import\s+') { $last = $i }
  }
  return $last
}

function Ensure-LineAfterFuture([string[]]$lines, [string]$exactLine) {
  foreach ($ln in $lines) { if ($ln.Trim() -eq $exactLine) { return $lines } }

  $ins = (Find-LastFutureIndex $lines) + 1
  if ($ins -lt 0) { $ins = 0 }

  $out = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($i -eq $ins) { $out.Add($exactLine) | Out-Null }
    $out.Add($lines[$i]) | Out-Null
  }
  if ($ins -ge $lines.Length) { $out.Add($exactLine) | Out-Null }
  return $out.ToArray()
}

function Ensure-DependsImported([string[]]$lines) {
  foreach ($ln in $lines) {
    if ($ln -match '^\s*from\s+fastapi\s+import\s+.*\bDepends\b') { return $lines }
  }

  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^\s*from\s+fastapi\s+import\s+') {
      if ($lines[$i] -notmatch '\bDepends\b') {
        $lines[$i] = $lines[$i].TrimEnd() + ", Depends"
      }
      return $lines
    }
  }

  return (Ensure-LineAfterFuture $lines "from fastapi import Depends")
}

function Patch-RouterDependencies([string[]]$lines) {
  # Patcht erste "router = APIRouter(" Zeile (oder beliebiger Variablenname)
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^\s*\w+\s*=\s*APIRouter\(') {
      if ($lines[$i] -match '\bdependencies\s*=') { return @{ lines=$lines; changed=$false } }
      # Inject direkt nach "("
      $lines[$i] = $lines[$i] -replace 'APIRouter\(', 'APIRouter(dependencies=[Depends(forbid_moderator)], '
      return @{ lines=$lines; changed=$true }
    }
  }
  return @{ lines=$lines; changed=$false }
}

# --- FIND CANDIDATES ---
$files = Get-ChildItem -Path $adminDir -Recurse -Filter "*.py"
$candidates = New-Object System.Collections.Generic.List[string]

foreach ($f in $files) {
  $p = $f.FullName
  $read = Read-Utf8PreserveBom $p
  $txt = [string]$read.text

  # Primär: Router prefix "/users"
  $isUsersRouter = $txt -match 'APIRouter\([^)]*prefix\s*=\s*["'']\/users["'']'
  # Fallback: spezifische Pfade
  $hasRolePaths = ($txt -match '["'']\/users\/\{user_id\}\/role["'']') -or ($txt -match '["'']\/users\/\{user_id\}\/moderator["'']')

  if ($isUsersRouter -or $hasRolePaths) {
    $candidates.Add($p) | Out-Null
  }
}

if ($candidates.Count -eq 0) {
  throw "Keine Admin-Users Router-Datei gefunden. Suche in app/admin nach APIRouter(prefix='/users') oder '/users/{user_id}/role'."
}

$changed = New-Object System.Collections.Generic.List[string]

foreach ($p in $candidates) {
  $read = Read-Utf8PreserveBom $p
  $orig = [string]$read.text
  $hasBom = [bool]$read.hasBom

  $lines = Split-Lines $orig

  # imports sicherstellen
  $lines = Ensure-LineAfterFuture $lines "from app.guards import forbid_moderator"
  $lines = Ensure-DependsImported $lines

  $patched = Patch-RouterDependencies $lines
  $lines2 = $patched.lines
  $did = [bool]$patched.changed

  $new = Join-Lines $lines2
  if ($new -ne $orig) {
    Write-Utf8PreserveBom $p $new $hasBom
    $changed.Add($p) | Out-Null
  } elseif ($did) {
    # (theoretisch) – falls Join gleich ist
    $changed.Add($p) | Out-Null
  }
}

if ($changed.Count -gt 0) {
  Ok "Admin-Users Router gefixt:"
  $changed | ForEach-Object { Write-Host " - $_" }
} else {
  Warn "Keine Änderungen geschrieben (evtl. bereits korrekt)."
}

Ok "FERTIG ✅"
