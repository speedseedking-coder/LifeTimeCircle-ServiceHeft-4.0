# server/scripts/ci_guard_required_job_pytest.ps1
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$WorkflowPath = ".github/workflows/ci.yml"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path -LiteralPath $WorkflowPath)) {
  Fail "Workflow nicht gefunden: $WorkflowPath (Repo-Root erwartet)"
}

# Zeilenbasiert lesen (robust)
$lines = Get-Content -LiteralPath $WorkflowPath -Encoding UTF8

# 1) jobs: muss existieren
if (-not ($lines | Select-String -Pattern '^\s*jobs\s*:\s*$')) {
  Fail "Kein 'jobs:' Block in $WorkflowPath gefunden."
}

# 2) Required Job-Key 'pytest:' muss existieren (2-space indent unter jobs)
$pytestIdx = $null
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s{2}pytest\s*:\s*$') {
    $pytestIdx = $i
    break
  }
}
if ($null -eq $pytestIdx) {
  Fail "Required Job-Key fehlt: 'jobs: -> pytest:' muss existieren (Branch Protection hängt daran)."
}

# 3) Ende des pytest-Jobs finden: nächster Job-Key auf 2-Space-Indent (z.B. '  web_build:')
$endIdx = $lines.Count
for ($k = $pytestIdx + 1; $k -lt $lines.Count; $k++) {
  if ($lines[$k] -match '^\s{2}[\w.-]+\s*:\s*$') {
    $endIdx = $k
    break
  }
}

# 4) Innerhalb des pytest-Jobs nach 'name: pytest' suchen (indent-unabhängig, akzeptiert Quotes)
#    Wichtig: NICHT '- name:' in steps matchen (da steht ein '-' vor name)
$hasName = $false
for ($j = $pytestIdx + 1; $j -lt $endIdx; $j++) {
  $line = $lines[$j]
  if ($line -match "^\s*name\s*:\s*['""]?pytest['""]?\s*(#.*)?$") {
    $hasName = $true
    break
  }
}

if (-not $hasName) {
  Write-Host "WARN: Im pytest-Job fehlt 'name: pytest'. Empfohlen für maximal stabile Check-Run-Namen." -ForegroundColor Yellow
}

Write-Host "OK: CI Guard – required job 'pytest' ist vorhanden." -ForegroundColor Green
exit 0