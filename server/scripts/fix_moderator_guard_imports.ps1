<#
Fix: Router benutzen Depends(forbid_moderator), aber Import fehlt -> NameError.

- Findet alle app/routers/**/*.py, die "Depends(forbid_moderator)" enthalten.
- Stellt sicher:
  - "from app.guards import forbid_moderator" ist vorhanden (nach __future__-Imports)
  - "Depends" ist aus fastapi importiert (entweder bestehende fastapi-importzeile erweitert oder neue Zeile)
- Verletzt niemals die __future__-Regel (future bleibt oben).
#>

param([switch]$WhatIf)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }
function Info($m){ Write-Host "$m" -ForegroundColor Cyan }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot    = Join-Path $serverRoot "app"
$routerDir  = Join-Path $appRoot "routers"

if (-not (Test-Path $routerDir)) { throw "routers/ nicht gefunden: $routerDir" }

function Find-LastFutureIndex([string[]]$lines) {
  $last = -1
  for ($i=0; $i -lt [Math]::Min(200, $lines.Length); $i++) {
    if ($lines[$i] -match '^\s*from\s+__future__\s+import\s+') { $last = $i }
  }
  return $last
}

function Ensure-GuardImportAfterFuture([string[]]$lines) {
  $guardRegex = '^\s*from\s+app\.guards\s+import\s+forbid_moderator\b.*$'
  $has = $false
  foreach ($ln in $lines) { if ($ln -match $guardRegex) { $has = $true; break } }

  # entferne alle bestehenden guard-imports (wir setzen ihn kontrolliert neu)
  $clean = New-Object System.Collections.Generic.List[string]
  foreach ($ln in $lines) {
    if ($ln -match $guardRegex) { continue }
    $clean.Add($ln) | Out-Null
  }

  if (-not $has) {
    $lastFuture = Find-LastFutureIndex $clean.ToArray()
    $insertAt = if ($lastFuture -ge 0) { $lastFuture + 1 } else { 0 }

    $out = New-Object System.Collections.Generic.List[string]
    for ($i=0; $i -lt $clean.Count; $i++) {
      if ($i -eq $insertAt) { $out.Add("from app.guards import forbid_moderator") | Out-Null }
      $out.Add($clean[$i]) | Out-Null
    }
    if ($insertAt -ge $clean.Count) { $out.Add("from app.guards import forbid_moderator") | Out-Null }
    return $out.ToArray()
  }

  # war vorhanden -> nur normalisiert (entfernt + wieder rein)
  $lastFuture2 = Find-LastFutureIndex $clean.ToArray()
  $insertAt2 = if ($lastFuture2 -ge 0) { $lastFuture2 + 1 } else { 0 }

  $out2 = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $clean.Count; $i++) {
    if ($i -eq $insertAt2) { $out2.Add("from app.guards import forbid_moderator") | Out-Null }
    $out2.Add($clean[$i]) | Out-Null
  }
  if ($insertAt2 -ge $clean.Count) { $out2.Add("from app.guards import forbid_moderator") | Out-Null }
  return $out2.ToArray()
}

function Ensure-DependsImport([string[]]$lines) {
  # Wenn already: from fastapi import ... Depends ...
  foreach ($ln in $lines) {
    if ($ln -match '^\s*from\s+fastapi\s+import\s+.*\bDepends\b') { return $lines }
  }

  # Wenn existiert: from fastapi import X -> ergänzen
  $out = @()
  $done = $false
  foreach ($ln in $lines) {
    if (-not $done -and $ln -match '^\s*from\s+fastapi\s+import\s+(?<rest>.+)$') {
      $rest = $Matches["rest"]
      if ($rest -match '\bDepends\b') {
        $out += $ln
      } else {
        $out += ($ln.TrimEnd() + ", Depends")
      }
      $done = $true
    } else {
      $out += $ln
    }
  }
  if ($done) { return $out }

  # Keine fastapi-importzeile: neue Zeile nach __future__
  $lastFuture = Find-LastFutureIndex $lines
  $insertAt = if ($lastFuture -ge 0) { $lastFuture + 1 } else { 0 }

  $out2 = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($i -eq $insertAt) { $out2.Add("from fastapi import Depends") | Out-Null }
    $out2.Add($lines[$i]) | Out-Null
  }
  if ($insertAt -ge $lines.Length) { $out2.Add("from fastapi import Depends") | Out-Null }

  return $out2.ToArray()
}

# --- run ---
$targets = Get-ChildItem -Path $routerDir -Recurse -Filter "*.py"
$changed = New-Object System.Collections.Generic.List[string]

foreach ($f in $targets) {
  $path = $f.FullName
  $orig = Get-Content -Path $path -Raw -Encoding UTF8

  if ($orig -notmatch 'Depends\s*\(\s*forbid_moderator\s*\)') { continue }

  $lines = $orig -split "`r?`n", 0, "SimpleMatch"

  $lines = Ensure-DependsImport $lines
  $lines = Ensure-GuardImportAfterFuture $lines

  $new = ($lines -join "`n")

  if ($new -ne $orig) {
    if ($WhatIf) {
      Info "WHATIF: würde fixen: $path"
    } else {
      Set-Content -Path $path -Value $new -Encoding UTF8
      $changed.Add($path) | Out-Null
    }
  }
}

if ($changed.Count -gt 0) {
  Ok "Fix angewendet auf:"
  $changed | ForEach-Object { Write-Host " - $_" }
} else {
  Warn "Keine Dateien mit Depends(forbid_moderator) gefunden oder keine Änderungen nötig."
}

Ok "FERTIG ✅"
