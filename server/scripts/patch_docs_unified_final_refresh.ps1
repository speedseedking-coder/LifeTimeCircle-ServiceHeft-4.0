# server/scripts/patch_docs_unified_final_refresh.ps1
# Idempotent (SAFE) Docs-Refresh Validator
# - macht KEINE Änderungen an bestehenden Docs
# - prüft: Required Docs vorhanden + Disclaimer exakt + Kernanker vorhanden
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

function Read-Raw([string]$path) {
  return Normalize-Lf (Get-Content -LiteralPath $path -Raw -ErrorAction Stop)
}

function Assert-File([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "MISSING: $path"
  }
  $raw = Read-Raw $path
  if ($raw.Trim().Length -lt 10) {
    throw "EMPTY/TOO SHORT: $path"
  }
  Write-Host "OK: present $path"
}

function Assert-Contains([string]$path, [string]$needle) {
  $raw = Read-Raw $path
  if ($raw -notlike "*$needle*") {
    throw "ASSERT FAILED: '$path' missing required text: $needle"
  }
  Write-Host "OK: $path contains required text."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot
Write-Host "Repo-Root: $repoRoot"

# Required docs
$required = @(
  "docs/01_DECISIONS.md",
  "docs/02_PRODUCT_SPEC_UNIFIED.md",
  "docs/03_RIGHTS_MATRIX.md",
  "docs/04_REPO_STRUCTURE.md",
  "docs/06_WORK_RULES.md",
  "docs/99_MASTER_CHECKPOINT.md"
)

foreach ($rel in $required) {
  Assert-File (Join-Path $repoRoot $rel)
}

# Invariants (Pflichttext exakt)
$disclaimer = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

Assert-Contains (Join-Path $repoRoot "docs/06_WORK_RULES.md") $disclaimer
Assert-Contains (Join-Path $repoRoot "docs/03_RIGHTS_MATRIX.md") $disclaimer
Assert-Contains (Join-Path $repoRoot "docs/02_PRODUCT_SPEC_UNIFIED.md") $disclaimer

# Kernanker (damit Specs nicht „vergessen“ werden)
Assert-Contains (Join-Path $repoRoot "docs/02_PRODUCT_SPEC_UNIFIED.md") "Unfalltrust"
Assert-Contains (Join-Path $repoRoot "docs/02_PRODUCT_SPEC_UNIFIED.md") "addon_first_enabled_at"
Assert-Contains (Join-Path $repoRoot "docs/03_RIGHTS_MATRIX.md") "Moderator"
Assert-Contains (Join-Path $repoRoot "docs/06_WORK_RULES.md") "deny-by-default"
Assert-Contains (Join-Path $repoRoot "docs/99_MASTER_CHECKPOINT.md") "docs/02_PRODUCT_SPEC_UNIFIED.md"

Write-Host "DONE: docs unified spec validated (no changes)."
