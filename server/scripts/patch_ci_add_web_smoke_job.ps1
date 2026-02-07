# server/scripts/patch_ci_add_web_smoke_job.ps1
# Adds a dedicated web build smoke job to .github/workflows/ci.yml (idempotent)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Robust: works both when executed as script and (not recommended) in interactive mode
$scriptRoot = $PSScriptRoot
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") {
  $scriptRoot = Split-Path -Parent $PSCommandPath
}
if (-not $scriptRoot -or $scriptRoot.Trim() -eq "") {
  $scriptRoot = (Get-Location).Path
}

$repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$ciPath   = Join-Path $repoRoot ".github\workflows\ci.yml"

if (-not (Test-Path -LiteralPath $ciPath)) {
  throw "CI workflow not found: $ciPath"
}

$raw = Get-Content -LiteralPath $ciPath -Raw

# Idempotence
if ($raw -match '(?m)^\s{2}web_smoke_build:\s*$') {
  Write-Host "OK: ci.yml already contains job 'web_smoke_build'." -ForegroundColor Green
  exit 0
}

$jobsMatch = [regex]::Match($raw, '(?m)^(?<indent>\s*)jobs:\s*$')
if (-not $jobsMatch.Success) {
  throw "Cannot find key 'jobs:' in ci.yml (unexpected format)."
}

$jobsIndent = $jobsMatch.Groups['indent'].Value
$jobIndent  = $jobsIndent + "  "

$jobLines = @(
"web_smoke_build:",
"  name: web smoke build (packages/web)",
"  runs-on: ubuntu-latest",
"  steps:",
"    - uses: actions/checkout@v4",
"    - name: Setup Node",
"      uses: actions/setup-node@v4",
"      with:",
"        node-version: '20'",
"        cache: 'npm'",
"        cache-dependency-path: packages/web/package-lock.json",
"    - name: Web build (toolkit)",
"      run: pwsh -NoProfile -ExecutionPolicy Bypass -File ./server/scripts/ltc_web_toolkit.ps1 -Smoke -Clean"
)

$jobBlock = ($jobLines | ForEach-Object { $jobIndent + $_ }) -join "`n"

# Insert directly after 'jobs:' line
$new = [regex]::Replace(
  $raw,
  '(?m)^(?<indent>\s*jobs:\s*)$',
  { param($m) $m.Value + "`n" + $jobBlock },
  1
)

if ($new -eq $raw) {
  Write-Host "OK: no changes needed." -ForegroundColor Green
  exit 0
}

Set-Content -LiteralPath $ciPath -Value ($new.TrimEnd() + "`n") -Encoding utf8NoBOM
Write-Host "OK: added job 'web_smoke_build' to $ciPath" -ForegroundColor Green
