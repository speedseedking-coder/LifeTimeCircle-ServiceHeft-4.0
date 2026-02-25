Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
  [switch]$SkipTests,
  [switch]$SkipIstCheck
)

function Invoke-Step {
  param([string]$Title, [scriptblock]$Block)
  Write-Host ""
  Write-Host "==> $Title" -ForegroundColor Cyan
  & $Block
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    throw "Step failed: $Title (exit=$LASTEXITCODE)"
  }
}

function Git([string[]]$Args) {
  $out = & git @Args
  if ($LASTEXITCODE -ne 0) { throw "git $($Args -join ' ') failed" }
  return ($out | Out-String).Trim()
}

# Always operate from repo root
$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root
[Environment]::CurrentDirectory = $root

# Facts
$branch = Git @("branch","--show-current")
$head   = Git @("rev-parse","HEAD")
$base   = Git @("rev-parse","origin/main")

# Quick range info (may be empty)
$commitList = Git @("log","--oneline","origin/main..HEAD")
$diffNames  = Git @("diff","--name-status","origin/main...HEAD")

# Optional checks
if (-not $SkipTests) {
  Invoke-Step "DoD: tools/test_all.ps1" { pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 }
} else {
  Write-Host ""
  Write-Host "==> Skipping tools/test_all.ps1 (per -SkipTests)" -ForegroundColor Yellow
}

if (-not $SkipIstCheck) {
  Invoke-Step "DoD: tools/ist_check.ps1" { pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1 }
} else {
  Write-Host ""
  Write-Host "==> Skipping tools/ist_check.ps1 (per -SkipIstCheck)" -ForegroundColor Yellow
}

# PR-ready snippet (copy/paste)
$ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
Write-Host ""
Write-Host "==================== COPY FOR PR ====================" -ForegroundColor Green
Write-Host "DoD:"
Write-Host "- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 => $(if($SkipTests){'SKIPPED'}else{'ALL GREEN ✅'})"
Write-Host "- pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1 => $(if($SkipIstCheck){'SKIPPED'}else{'DONE ✅'})"
Write-Host ""
Write-Host "Evidence:"
Write-Host "- Timestamp: $ts"
Write-Host "- Branch: $branch"
Write-Host "- HEAD: $head"
Write-Host "- Base (origin/main): $base"
Write-Host "- Commits (origin/main..HEAD):"
if ([string]::IsNullOrWhiteSpace($commitList)) { Write-Host "  - (none)" } else { $commitList.Split("`n") | ForEach-Object { Write-Host "  - $_" } }
Write-Host "- Changed files (origin/main...HEAD):"
if ([string]::IsNullOrWhiteSpace($diffNames)) { Write-Host "  - (none)" } else { $diffNames.Split("`n") | ForEach-Object { Write-Host "  - $_" } }
Write-Host "================== /COPY FOR PR =====================" -ForegroundColor Green
