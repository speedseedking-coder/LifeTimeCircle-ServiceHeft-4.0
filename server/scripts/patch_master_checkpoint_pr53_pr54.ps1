[CmdletBinding()]
param(
  [string]$Master = "docs/99_MASTER_CHECKPOINT.md",
  [string]$Date = "2026-02-06",
  [string]$Timezone = "Europe/Berlin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  try {
    $root = (git rev-parse --show-toplevel 2>$null).Trim()
    if ($LASTEXITCODE -eq 0 -and $root) { return $root }
  } catch {}
  if ($PSScriptRoot) { return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path }
  return (Get-Location).Path
}

function Read-Utf8NoBom {
  param([Parameter(Mandatory=$true)][string]$p)
  if (-not (Test-Path -LiteralPath $p)) { throw "File not found: $p" }
  [byte[]]$bytes = [System.IO.File]::ReadAllBytes($p)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    if ($bytes.Length -eq 3) { return "" }
    $bytes = $bytes[3..($bytes.Length-1)]
  }
  return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory=$true)][string]$p,
    [Parameter(Mandatory=$true)][string]$t
  )
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($p, $t, $enc)
}

$RepoRoot = Get-RepoRoot
$MasterPath = if ([System.IO.Path]::IsPathRooted($Master)) { $Master } else { Join-Path $RepoRoot $Master }

$text = Read-Utf8NoBom -p $MasterPath
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }

# Stand: **YYYY-MM-DD** (Timezone) setzen (idempotent)
$standLine = "Stand: **$Date** ($Timezone)"
$text2 = [regex]::Replace(
  $text,
  "(?m)^\s*Stand:\s*\*\*\d{4}-\d{2}-\d{2}\*\*.*$",
  $standLine
)

# Einträge nur ergänzen, wenn nicht vorhanden
$need53 = -not ([regex]::IsMatch($text2, "(?m)PR\s*#53\b"))
$need54 = -not ([regex]::IsMatch($text2, "(?m)PR\s*#54\b"))

$insertLines = @()
if ($need54) {
  # Single-Quotes absichtlich: Backticks sollen literal bleiben (Markdown)
  $insertLines += '✅ PR #54 gemerged: `fix(web): add mandatory Public QR disclaimer`'
  $insertLines += '✅ Public QR: Pflichttext (exakt) in `packages/web/src/pages/PublicQrPage.tsx`'
  $insertLines += '✅ Script: `server/scripts/patch_public_qr_disclaimer.ps1` (idempotent)'
}
if ($need53) {
  $insertLines += '✅ PR #53 gemerged: `chore(web): add web smoke toolkit script`'
  $insertLines += '✅ Public QR Landing: `packages/web/src/pages/PublicQrPage.tsx` + App-Route `/qr/<vehicleId>`'
  $insertLines += '✅ Script: `server/scripts/ltc_web_toolkit.ps1` (quiet kill-node; optional -Clean; npm ci + build)'
}

if ($insertLines.Count -gt 0) {
  $insertBlock = ($insertLines -join $nl) + $nl + $nl

  $marker = "Aktueller Stand (main)"
  $idx = $text2.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
  if ($idx -lt 0) { throw "Marker not found: '$marker' in $MasterPath" }

  # Insert direkt nach der Überschrift-Zeile
  $lineEnd = $text2.IndexOf($nl, $idx)
  if ($lineEnd -lt 0) { $lineEnd = $idx + $marker.Length }
  $insertPos = $lineEnd + $nl.Length

  $text2 = $text2.Insert($insertPos, $insertBlock)
}

if ($text2 -eq $text) {
  Write-Host "OK: no changes needed."
  return
}

Write-Utf8NoBom -p $MasterPath -t $text2

# Verify
$after = Read-Utf8NoBom -p $MasterPath
if (-not ($after -match ("(?m)^\s*Stand:\s*\*\*{0}\*\*.*$" -f [regex]::Escape($Date)))) {
  throw "Patch failed: Stand not updated to $Date."
}
if ($need53 -and -not ($after -match "(?m)PR\s*#53\b")) { throw "Patch failed: PR #53 missing after write." }
if ($need54 -and -not ($after -match "(?m)PR\s*#54\b")) { throw "Patch failed: PR #54 missing after write." }

Write-Host "OK: patched $MasterPath (PR #53/#54 + Stand $Date)."
