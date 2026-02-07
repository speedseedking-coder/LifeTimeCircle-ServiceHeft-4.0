# server/scripts/verify_ci_branch_protection.ps1
# LifeTimeCircle – Service Heft 4.0
# Verify: Branch Protection required checks + Check-Runs (Job-Namen, nicht UI-Labels)
# Stand: 2026-02-07
# Policy: deny-by-default; SoT docs; CI required check must be "pytest" (job name)

[CmdletBinding()]
param(
  [string]$Branch = "main",
  [string]$RequiredJobName = "pytest",
  [switch]$CheckHeadRun = $true,
  [switch]$VerboseJson = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

function Info([string]$msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

function Warn([string]$msg) {
  Write-Host "WARN: $msg" -ForegroundColor Yellow
}

function Require-Cmd([string]$name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Fail "Missing required command '$name'. Install/enable it and retry."
  }
}

Require-Cmd "git"
Require-Cmd "gh"

# Ensure inside a git repo
try {
  git rev-parse --show-toplevel | Out-Null
} catch {
  Fail "Not inside a git repository. Run from repo root."
}

# Resolve repo (OWNER/REPO)
$repo = ""
try {
  $repo = (gh repo view --json nameWithOwner --jq ".nameWithOwner").Trim()
} catch {
  Fail "Cannot resolve GitHub repo via 'gh repo view'. Are you authenticated (gh auth login) and in the correct repo?"
}
if ([string]::IsNullOrWhiteSpace($repo)) {
  Fail "Resolved repo is empty."
}

Write-Host "Repo: $repo"
Write-Host "Branch: $Branch"
Write-Host "Required job name: $RequiredJobName"
Write-Host ""

# 1) Branch protection required_status_checks
$requiredStatusChecksJson = $null
try {
  $requiredStatusChecksJson = gh api "repos/$repo/branches/$Branch/protection/required_status_checks" 2>$null
} catch {
  Fail "Failed to read branch protection required_status_checks. Ensure you have permission and that branch protection is enabled."
}

if ($VerboseJson) {
  Write-Host "DEBUG required_status_checks JSON:" -ForegroundColor Cyan
  Write-Host $requiredStatusChecksJson
  Write-Host ""
}

$required = $null
try {
  $required = $requiredStatusChecksJson | ConvertFrom-Json
} catch {
  Fail "Failed to parse required_status_checks JSON."
}

if ($null -eq $required) {
  Fail "required_status_checks returned null."
}

# strict should be true
if ($required.strict -ne $true) {
  Fail "Branch protection required_status_checks.strict is not true (actual: $($required.strict)). Expected: true."
}

# contexts OR checks must include RequiredJobName
$contexts = @()
$checks = @()

if ($null -ne $required.contexts) {
  $contexts = @($required.contexts | ForEach-Object { "$_".Trim() } | Where-Object { $_ -ne "" })
}

if ($null -ne $required.checks) {
  # checks is array of { context, app_id }
  $checks = @($required.checks | ForEach-Object { "$($_.context)".Trim() } | Where-Object { $_ -ne "" })
}

$hasInContexts = $contexts -contains $RequiredJobName
$hasInChecks = $checks -contains $RequiredJobName

if (-not ($hasInContexts -or $hasInChecks)) {
  $ctxDump = if ($contexts.Count -gt 0) { $contexts -join ", " } else { "(none)" }
  $chkDump = if ($checks.Count -gt 0) { $checks -join ", " } else { "(none)" }
  Fail "Required check '$RequiredJobName' not found in branch protection. contexts=[$ctxDump], checks=[$chkDump]"
}

Info "Branch protection strict=true"
Info "Branch protection requires '$RequiredJobName' (via contexts/checks)"

# 2) Optional: Verify HEAD check-run 'pytest' exists + success
if ($CheckHeadRun) {
  $sha = ""
  try {
    $sha = (git rev-parse HEAD).Trim()
  } catch {
    Fail "Failed to resolve HEAD SHA."
  }

  if ([string]::IsNullOrWhiteSpace($sha)) {
    Fail "HEAD SHA is empty."
  }

  Write-Host ""
  Write-Host "HEAD: $sha"

  # Check-runs are the source of truth; commit status API may be empty.
  $checkRunsJson = $null
  try {
    $checkRunsJson = gh api "repos/$repo/commits/$sha/check-runs" 2>$null
  } catch {
    Fail "Failed to query check-runs for HEAD. Ensure GitHub API access via gh works."
  }

  if ($VerboseJson) {
    Write-Host "DEBUG check-runs JSON:" -ForegroundColor Cyan
    Write-Host $checkRunsJson
    Write-Host ""
  }

  $checkRuns = $null
  try {
    $checkRuns = $checkRunsJson | ConvertFrom-Json
  } catch {
    Fail "Failed to parse check-runs JSON."
  }

  if ($null -eq $checkRuns -or $null -eq $checkRuns.check_runs) {
    Fail "check-runs payload missing 'check_runs'."
  }

  $runs = @($checkRuns.check_runs)
  if ($runs.Count -eq 0) {
    Fail "No check-runs found on HEAD. CI may not have executed for this commit yet."
  }

  $pytestRuns = @($runs | Where-Object { $_.name -eq $RequiredJobName })

  if ($pytestRuns.Count -eq 0) {
    $names = @($runs | ForEach-Object { $_.name } | Sort-Object -Unique)
    Fail "No check-run named '$RequiredJobName' on HEAD. Found: $($names -join ', ')"
  }

  # If multiple, pick the latest by completed_at / started_at
  $selected = $pytestRuns |
    Sort-Object -Property @{Expression = { $_.completed_at }; Descending = $true }, @{Expression = { $_.started_at }; Descending = $true } |
    Select-Object -First 1

  $status = "$($selected.status)".Trim()
  $conclusion = "$($selected.conclusion)".Trim()

  if ($status -ne "completed") {
    Fail "Check-run '$RequiredJobName' is not completed (status=$status)."
  }
  if ($conclusion -ne "success") {
    Fail "Check-run '$RequiredJobName' did not succeed (conclusion=$conclusion)."
  }

  Info "HEAD check-run '$RequiredJobName' completed=completed conclusion=success"
}

Write-Host ""
Info "All CI / Branch Protection checks verified."
exit 0