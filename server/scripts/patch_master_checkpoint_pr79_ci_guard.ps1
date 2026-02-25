param(
  [string]$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Set-Location $RepoRoot
[Environment]::CurrentDirectory = $RepoRoot

$enc = New-Object System.Text.UTF8Encoding($false)
$cpPath = Join-Path $RepoRoot "docs/99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $cpPath)) {
  Write-Host ("SKIP: {0} not found" -f $cpPath) -ForegroundColor Yellow
  exit 0
}

$cp = [IO.File]::ReadAllText($cpPath, $enc)

# Idempotent: wenn schon drin, no-op
if ($cp -match "PR\s*#79" -or $cp -match "patch_master_checkpoint_pr79_ci_guard\.ps1") {
  Write-Host "OK: already present (no-op)" -ForegroundColor Green
  exit 0
}

$appendLines = @(
  ""
  "PR #79 merged: CI Guard required check pytest stabilized"
  "- Script: server/scripts/patch_master_checkpoint_pr79_ci_guard.ps1"
  ""
)

$append = ($appendLines -join "`n")

[IO.File]::WriteAllText($cpPath, ($cp.TrimEnd() + "`n" + $append), $enc)
Write-Host "OK: appended PR79 note to master checkpoint" -ForegroundColor Green
