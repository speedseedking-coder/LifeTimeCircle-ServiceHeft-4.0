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

$raw = Get-Content -LiteralPath $WorkflowPath -Raw -Encoding UTF8

# 1) jobs: muss existieren
if ($raw -notmatch "(?m)^\s*jobs\s*:\s*$") {
  Fail "Kein 'jobs:' Block in $WorkflowPath gefunden."
}

# 2) Required Job-Key 'pytest:' muss existieren (Branch-Protection hängt daran)
if ($raw -notmatch "(?m)^\s{2}pytest\s*:\s*$") {
  Fail "Required Job-Key fehlt: 'jobs: -> pytest:' muss existieren (Branch Protection hängt daran)."
}

# 3) pytest-Job-Block robust extrahieren:
#    Ende NICHT bei '2 spaces + irgendwas' (würde Kommentare treffen),
#    sondern nur bei '2 spaces + <jobId>:' (echter nächster Job-Key)
$pytestBlockMatch = [regex]::Match(
  $raw,
  "(?ms)^\s{2}pytest\s*:\s*$\s*(?<body>.*?)(?=^\s{2}[\w.-]+\s*:\s*$|\z)"
)

if (-not $pytestBlockMatch.Success) {
  Fail "Konnte pytest-Job-Block nicht sauber extrahieren (unerwartetes Workflow-Format)."
}

$body = $pytestBlockMatch.Groups["body"].Value

# 4) Empfehlung: explizit 'name: pytest' im pytest-Job (akzeptiert Quotes)
if ($body -notmatch "(?m)^\s{4,}name\s*:\s*['""]?pytest['""]?\s*$") {
  Write-Host "WARN: Im pytest-Job fehlt 'name: pytest'. Empfohlen für maximal stabile Check-Run-Namen." -ForegroundColor Yellow
}

Write-Host "OK: CI Guard – required job 'pytest' ist vorhanden." -ForegroundColor Green
exit 0