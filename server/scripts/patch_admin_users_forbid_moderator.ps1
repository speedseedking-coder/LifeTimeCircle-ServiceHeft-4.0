# server/scripts/patch_admin_users_forbid_moderator.ps1
<#
P1 Fix: /admin/users* muss forbid_moderator bekommen.

Patch-Ziel: app/admin/routes.py
- Fügt (falls nötig) Imports hinzu:
  - from app.guards import forbid_moderator
  - Depends (in from fastapi import ... oder als eigene Zeile)
- Patcht include_router(...) Aufrufe, die prefix "/users" oder "/admin/users" setzen:
  -> dependencies=[Depends(forbid_moderator)]
- NICHT patchen, wenn prefix /blog oder /news
- BOM-safe UTF-8
#>

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$targetPath = Join-Path $serverRoot "app\admin\routes.py"
if (-not (Test-Path $targetPath)) { throw "Zieldatei nicht gefunden: $targetPath" }

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

function Find-MatchingParen([string]$s, [int]$openIdx) {
  $depth = 0
  $inSingle = $false
  $inDouble = $false
  $escape = $false

  for ($i=$openIdx; $i -lt $s.Length; $i++) {
    $ch = $s[$i]

    if ($escape) { $escape = $false; continue }
    if ($ch -eq '\') { $escape = $true; continue }

    if (-not $inDouble -and $ch -eq "'") { $inSingle = -not $inSingle; continue }
    if (-not $inSingle -and $ch -eq '"') { $inDouble = -not $inDouble; continue }

    if ($inSingle -or $inDouble) { continue }

    if ($ch -eq '(') { $depth++; continue }
    if ($ch -eq ')') {
      $depth--
      if ($depth -eq 0) { return $i }
    }
  }
  return -1
}

function Patch-IncludeRouterUsers([string]$text) {
  $changed = $false
  $idx = 0

  while ($true) {
    $start = $text.IndexOf("include_router(", $idx)
    if ($start -lt 0) { break }

    $open = $start + "include_router".Length
    if ($open -ge $text.Length -or $text[$open] -ne "(") { $idx = $start + 1; continue }

    $close = Find-MatchingParen $text $open
    if ($close -lt 0) { break }

    $args = $text.Substring($open + 1, $close - $open - 1)

    # nur /users oder /admin/users
    $isUsers = ($args -match 'prefix\s*=\s*["'']\/users["'']') -or ($args -match 'prefix\s*=\s*["'']\/admin\/users["'']')
    if (-not $isUsers) { $idx = $close + 1; continue }

    # blog/news nicht anfassen
    if ($args -match 'prefix\s*=\s*["'']\/(blog|news)["'']') { $idx = $close + 1; continue }

    # schon dependencies?
    if ($args -match '\bdependencies\s*=') { $idx = $close + 1; continue }

    $newArgs = $args.TrimEnd()
    if (-not [string]::IsNullOrWhiteSpace($newArgs) -and -not $newArgs.TrimEnd().EndsWith(",")) { $newArgs += "," }
    $newArgs += " dependencies=[Depends(forbid_moderator)]"

    $text = $text.Substring(0, $open + 1) + $newArgs + $text.Substring($close)
    $changed = $true
    $idx = $open + 1 + $newArgs.Length + 1
  }

  return @($text, $changed)
}

# --- RUN ---
$read = Read-Utf8PreserveBom $targetPath
$orig = [string]$read.text
$hasBom = [bool]$read.hasBom

$lines = Split-Lines $orig
$lines = Ensure-LineAfterFuture $lines "from app.guards import forbid_moderator"
$lines = Ensure-DependsImported $lines
$text1 = Join-Lines $lines

$res = Patch-IncludeRouterUsers $text1
$newText = $res[0]
$didPatch = [bool]$res[1]

if ($newText -ne $orig) {
  Write-Utf8PreserveBom $targetPath $newText $hasBom
  if ($didPatch) { Ok "admin/routes.py gepatcht: include_router(prefix=/users) mit forbid_moderator abgesichert" }
  else { Ok "admin/routes.py nur Imports normalisiert" }
} else {
  Warn "admin/routes.py: keine Änderungen nötig"
}

Ok "FERTIG ✅"
