# server/scripts/patch_master_checkpoint_pr89_node_engines.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Resolve-Path (Join-Path $scriptDir "..\..") | Select-Object -ExpandProperty Path

$checkpoint = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"
if (-not (Test-Path $checkpoint)) { throw "ERROR: Datei nicht gefunden: $checkpoint" }

$raw = [System.IO.File]::ReadAllText($checkpoint, [System.Text.UTF8Encoding]::new($false))
$raw = $raw -replace "`r`n", "`n"

# Stand-Datum auf heute (nur erstes Vorkommen)
$today = (Get-Date).ToString("yyyy-MM-dd")
$raw = [regex]::Replace(
  $raw,
  "(?m)^Stand:\s*\*\*\d{4}-\d{2}-\d{2}\*\*",
  ("Stand: **{0}**" -f $today),
  1
)

# Idempotenz
if ($raw -match "PR\s*#89") {
  Write-Host "OK: Master Checkpoint enthält PR #89 bereits."
  exit 0
}

$entry = @"
✅ PR #89 gemerged: `chore(web): declare node engine >=20.19.0 (vite 7)`
- `packages/web/package.json`: `engines.node` auf `>=20.19.0` gesetzt (Vite 7 Requirement / verhindert lokale Mismatch-Setups)

"@ -replace "`r`n", "`n"

$marker = "## Aktueller Stand (main)"
$idx = $raw.IndexOf($marker)
if ($idx -lt 0) { throw "ERROR: Marker nicht gefunden: '$marker'" }

$after = $idx + $marker.Length
$lineEnd = $raw.IndexOf("`n", $after)
if ($lineEnd -lt 0) { $lineEnd = $raw.Length }
$insertPos = $lineEnd + 1

if ($insertPos -lt $raw.Length) {
  if ($raw.Substring($insertPos, [Math]::Min(2, $raw.Length - $insertPos)) -ne "`n`n") {
    $raw = $raw.Insert($insertPos, "`n")
  }
}

$raw = $raw.Insert($insertPos, $entry)
$raw = $raw.TrimEnd("`n") + "`n"

Write-Utf8NoBom -Path $checkpoint -Content $raw
Write-Host "OK: Master Checkpoint gepatcht (PR #89 + engines.node Hinweis)."