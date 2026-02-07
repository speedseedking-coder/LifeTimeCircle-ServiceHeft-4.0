# server/scripts/patch_master_checkpoint_pr87_vite7_esbuild_audit.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Resolve-Path (Join-Path $scriptDir "..\..") | Select-Object -ExpandProperty Path

$checkpoint = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"
if (-not (Test-Path $checkpoint)) {
  throw "ERROR: Datei nicht gefunden: $checkpoint"
}

$raw = [System.IO.File]::ReadAllText($checkpoint, [System.Text.UTF8Encoding]::new($false))
$raw = $raw -replace "`r`n", "`n"

# Stand-Datum auf "heute" setzen (nur erstes Vorkommen)
$today = (Get-Date).ToString("yyyy-MM-dd")
$raw = [regex]::Replace(
  $raw,
  "(?m)^Stand:\s*\*\*\d{4}-\d{2}-\d{2}\*\*",
  ("Stand: **{0}**" -f $today),
  1
)

# Idempotenz: wenn PR #87 schon drin ist -> OK
if ($raw -match "PR\s*#87") {
  Write-Host "OK: Master Checkpoint enthält PR #87 bereits."
  exit 0
}

$entry = @"
✅ PR #87 gemerged: `chore(web): bump vite to 7.3.1 (esbuild GHSA-67mh-4wv8-2f99)`
- Fix dev-only Audit: esbuild Advisory GHSA-67mh-4wv8-2f99 (via Vite 7)
- Hinweis: Vite 7 benötigt Node.js >= 20.19

"@ -replace "`r`n", "`n"

# 1) In "Aktueller Stand (main)" direkt nach der Heading-Zeile einfügen
$marker = "## Aktueller Stand (main)"
$idx = $raw.IndexOf($marker)
if ($idx -lt 0) {
  throw "ERROR: Marker nicht gefunden: '$marker' in docs/99_MASTER_CHECKPOINT.md"
}

$after = $idx + $marker.Length
$lineEnd = $raw.IndexOf("`n", $after)
if ($lineEnd -lt 0) { $lineEnd = $raw.Length }
$insertPos = $lineEnd + 1

# sicherstellen, dass ein Leerzeilenblock nach dem Heading existiert
if ($insertPos -lt $raw.Length) {
  if ($raw.Substring($insertPos, [Math]::Min(2, $raw.Length - $insertPos)) -ne "`n`n") {
    $raw = $raw.Insert($insertPos, "`n")
  }
}

$raw = $raw.Insert($insertPos, $entry)

# 2) Optional: Node-Hinweis auch bei "Gotchas:" ergänzen (falls vorhanden)
if ($raw -notmatch "Node\.js\s*>=\s*20\.19") {
  $gotchas = "Gotchas:"
  $gidx = $raw.IndexOf($gotchas)
  if ($gidx -ge 0) {
    $gAfter = $gidx + $gotchas.Length
    $gLineEnd = $raw.IndexOf("`n", $gAfter)
    if ($gLineEnd -lt 0) { $gLineEnd = $raw.Length }
    $gInsertPos = $gLineEnd + 1
    $nodeLine = "- Web Toolchain: Node.js >= 20.19 (Vite 7 requirement)`n"
    $raw = $raw.Insert($gInsertPos, $nodeLine)
  }
}

$raw = $raw.TrimEnd("`n") + "`n"
Write-Utf8NoBom -Path $checkpoint -Content $raw
Write-Host "OK: Master Checkpoint gepatcht (PR #87 + Node-Hinweis)."