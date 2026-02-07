# server/scripts/verify_ci_all.ps1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "== LTC CI Verify (ALL) ==" -ForegroundColor Cyan

# 1) Workflow-Guard (lokal) – prüft, dass required job key 'pytest' im Workflow existiert
& pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ci_guard_required_job_pytest.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2) Branch-Protection + HEAD check-run verifizieren (GitHub API)
& pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\verify_ci_branch_protection.ps1
exit $LASTEXITCODE