# server/scripts/patch_master_checkpoint_pr60_pr61.ps1
# Idempotent Patch:
# - docs/99_MASTER_CHECKPOINT.md: Stand -> 2026-02-07 (Europe/Berlin)
# - entfernt "## In Arbeit (dieser Branch) ..." Block (falls vorhanden)
# - fügt PR #60/#61 unter "## Aktueller Stand (main)" ein (ohne Duplikate)
# PowerShell 7+

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Lf([string]$s) {
  if ($null -eq $s) { return "`n" }
  $s = $s -replace "`r`n", "`n"
  $s = $s -replace "`r", "`n"
  if (-not $s.EndsWith("`n")) { $s += "`n" }
  return $s
}

function Read-File([string]$path) {
  return Normalize-Lf (Get-Content -LiteralPath $path -Raw -ErrorAction Stop)
}

function Write-Utf8NoBom([string]$path, [string]$content) {
  $content = Normalize-Lf $content
  [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
}

function Get-RepoRoot([string]$fallbackPath) {
  try {
    $top = (& git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $top -and $top.Trim().Length -gt 0) {
      return (Resolve-Path $top.Trim())
    }
  } catch { }
  return (Resolve-Path $fallbackPath)
}

$basePath = if ($PSScriptRoot -and $PSScriptRoot.Trim().Length -gt 0) {
  (Join-Path $PSScriptRoot "..\..")
} else {
  (Get-Location).Path
}

$repoRoot = Get-RepoRoot $basePath
Set-Location $repoRoot

$mcPath = Join-Path $repoRoot "docs/99_MASTER_CHECKPOINT.md"
$raw = Read-File $mcPath
$orig = $raw

# Stand aktualisieren (nur die Master-Header-Zeile)
$raw = [regex]::Replace(
  $raw,
  '(?ms)^\# docs/99_MASTER_CHECKPOINT\.md\s*\n\# LifeTimeCircle – Service Heft 4\.0\s*\n\*\*MASTER CHECKPOINT \(SoT\)\*\*\s*\nStand:\s*\*\*.*?\*\*.*?\n',
  "# docs/99_MASTER_CHECKPOINT.md`n# LifeTimeCircle – Service Heft 4.0`n**MASTER CHECKPOINT (SoT)**`nStand: **2026-02-07** (Europe/Berlin)`n"
)

# "In Arbeit (dieser Branch)" Block entfernen (falls vorhanden)
$raw = [regex]::Replace(
  $raw,
  '(?s)\n## In Arbeit \(dieser Branch\).*?(?=\n## |\z)',
  "`n"
)

# Bestehende PR #60/#61 Einträge entfernen (idempotent)
$raw = [regex]::Replace($raw, '(?m)^\s*✅\s*PR\s*#60.*(?:\n(?!\s*✅\s*PR\s*#\d+).*)*', '')
$raw = [regex]::Replace($raw, '(?m)^\s*✅\s*PR\s*#61.*(?:\n(?!\s*✅\s*PR\s*#\d+).*)*', '')

$insert = @"
✅ PR #60 gemerged: `docs: unify final spec (userflow/trust/pii/modules/transfer/pdfs/notifications/import)`
- Neue SoT Datei: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Updates: `docs/01_DECISIONS.md`, `docs/03_RIGHTS_MATRIX.md`, `docs/04_REPO_STRUCTURE.md`, `docs/06_WORK_RULES.md`, `docs/99_MASTER_CHECKPOINT.md`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` (Validator; idempotent; keine Änderungen an bestehenden Docs)

✅ PR #61 gemerged: `fix(scripts): make docs unified refresh patch script parseable + safe`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` ist jetzt parsebar und prüft Pflicht-Disclaimer + Kernanker (keine Doc-Rewrites)

"@

if ($raw -notmatch '(?m)^## Aktueller Stand \(main\)\s*$') {
  throw "MASTER_CHECKPOINT missing header: ## Aktueller Stand (main)"
}

# Insert direkt nach Header
$raw = [regex]::Replace(
  $raw,
  '(?m)^## Aktueller Stand \(main\)\s*$',
  ("## Aktueller Stand (main)`n" + $insert).TrimEnd()
)

$raw = Normalize-Lf $raw

if ($raw -eq $orig) {
  Write-Host "OK: no changes needed."
  exit 0
}

Write-Utf8NoBom $mcPath $raw
Write-Host "UPDATED: docs/99_MASTER_CHECKPOINT.md"
