# server/scripts/fix_future_and_forbid_imports.ps1
<#
Fix: __future__-Imports korrekt platzieren + forbid_moderator/Depends vor erster Nutzung sicherstellen.
BOM-safe.

- Bearbeitet NUR app/routers/**/*.py
- Skip: auth.py, public_qr.py, news.py, blog.py
- Nur Dateien, die Depends(forbid_moderator) enthalten
- Ergebnis:
  preamble (shebang/encoding/docstring) +
  __future__ imports +
  from app.guards import forbid_moderator (+ ggf. from fastapi import Depends) +
  rest
#>

param([switch]$WhatIf)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$routerDir  = Join-Path $serverRoot "app\routers"
if (-not (Test-Path $routerDir)) { throw "routers/ nicht gefunden: $routerDir" }

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

function Is-BlankOrComment([string]$ln) {
  $t = $ln.Trim()
  return ($t -eq "" -or $t.StartsWith("#"))
}

function Find-PreambleEnd([string[]]$lines) {
  $i = 0

  if ($lines.Length -gt 0 -and $lines[0].StartsWith("#!")) { $i = 1 }
  if ($lines.Length -gt $i -and $lines[$i] -match 'coding[:=]\s*[-\w]+' ) { $i++ }

  while ($i -lt $lines.Length -and (Is-BlankOrComment $lines[$i])) { $i++ }

  if ($i -lt $lines.Length) {
    $t = $lines[$i].Trim()
    $q = $null
    if ($t.StartsWith('"""')) { $q = '"""' }
    elseif ($t.StartsWith("'''")) { $q = "'''" }

    if ($q) {
      if ($t.Length -gt 3 -and $t.Substring(3).Contains($q)) {
        $i++
      } else {
        $i++
        while ($i -lt $lines.Length -and -not $lines[$i].Contains($q)) { $i++ }
        if ($i -lt $lines.Length) { $i++ }
      }
      while ($i -lt $lines.Length -and (Is-BlankOrComment $lines[$i])) { $i++ }
    }
  }

  return $i
}

function Extract-Future([string[]]$lines) {
  $future = New-Object System.Collections.Generic.List[string]
  $rest   = New-Object System.Collections.Generic.List[string]

  foreach ($ln in $lines) {
    if ($ln.TrimStart() -match '^from\s+__future__\s+import\s+') {
      $future.Add($ln.TrimEnd()) | Out-Null
    } else {
      $rest.Add($ln) | Out-Null
    }
  }

  return @{ future = $future; rest = $rest }
}

function Remove-MatchingLines([System.Collections.Generic.List[string]]$lines, [string]$regex) {
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($ln in $lines) {
    if ($ln -match $regex) { continue }
    $out.Add($ln) | Out-Null
  }
  return $out
}

function Has-DependsImported([System.Collections.Generic.List[string]]$lines) {
  foreach ($ln in $lines) {
    if ($ln -match '^\s*from\s+fastapi\s+import\s+.*\bDepends\b') { return $true }
    if ($ln -match '^\s*import\s+fastapi\b' ) { return $true } # selten, aber dann evtl fastapi.Depends genutzt
  }
  return $false
}

$files = Get-ChildItem -Path $routerDir -Recurse -Filter "*.py"
$changed = New-Object System.Collections.Generic.List[string]

foreach ($f in $files) {
  $name = $f.Name.ToLowerInvariant()
  if ($SKIP -contains $name) { continue }

  $path = $f.FullName
  $read = Read-Utf8PreserveBom $path
  $orig = [string]$read.text
  $hasBom = [bool]$read.hasBom

  if ($orig -notmatch 'Depends\s*\(\s*forbid_moderator\s*\)') { continue }

  $lines = Split-Lines $orig
  $pEnd = Find-PreambleEnd $lines

  $preamble = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $pEnd; $i++) { $preamble.Add($lines[$i]) | Out-Null }

  $body = New-Object System.Collections.Generic.List[string]
  for ($i=$pEnd; $i -lt $lines.Length; $i++) { $body.Add($lines[$i]) | Out-Null }

  $ex = Extract-Future $body.ToArray()
  $future = $ex.future
  $rest   = $ex.rest

  # Alte guard-imports entfernen (egal wo)
  $rest = Remove-MatchingLines $rest '^\s*from\s+app\.guards\s+import\s+forbid_moderator\b.*$'
  # Alte "from fastapi import Depends" (single-line) entfernen (wir fügen ggf. neu ein)
  $rest = Remove-MatchingLines $rest '^\s*from\s+fastapi\s+import\s+Depends\s*$'

  $header = New-Object System.Collections.Generic.List[string]
  $header.Add("from app.guards import forbid_moderator") | Out-Null

  if (-not (Has-DependsImported $rest)) {
    $header.Add("from fastapi import Depends") | Out-Null
  }

  # Zusammensetzen ohne String-Enumerable-Fallen
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($ln in $preamble) { $out.Add($ln) | Out-Null }
  foreach ($ln in $future)   { $out.Add($ln) | Out-Null }
  foreach ($ln in $header)   { $out.Add($ln) | Out-Null }
  foreach ($ln in $rest)     { $out.Add($ln) | Out-Null }

  $newText = Join-Lines $out.ToArray()

  if ($newText -ne $orig) {
    if ($WhatIf) {
      Write-Host "WHATIF: würde fixen: $path"
    } else {
      Write-Utf8PreserveBom $path $newText $hasBom
      $changed.Add($path) | Out-Null
    }
  }
}

if ($changed.Count -gt 0) {
  Ok "Gefixte Router-Dateien:"
  $changed | ForEach-Object { Write-Host " - $_" }
} else {
  Warn "Keine Dateien gefixt (keine Matches oder schon ok)."
}

Ok "FERTIG ✅"
