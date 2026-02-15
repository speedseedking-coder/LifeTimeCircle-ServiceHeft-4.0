# tools/test_all.ps1
# One-command green: backend tests + web build
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host ""; Write-Host "==> $msg" }

function Run-Step([string]$name, [scriptblock]$fn) {
  try { Step $name; & $fn; Write-Host "OK: $name"; return $true }
  catch { Write-Host "FAIL: $name"; Write-Host $_; return $false }
}

$repoRoot = (git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot) { throw "Not inside a git repo (git rev-parse failed)." }
Set-Location $repoRoot

$ok = $true

$ok = $ok -and (Run-Step "Backend tests (server): poetry run pytest -q" {
  Push-Location "server"
  try { poetry run pytest -q } finally { Pop-Location }
})

$ok = $ok -and (Run-Step "Web build (packages/web): npm ci + npm run build" {
  Push-Location "packages/web"
  try { npm ci; npm run build } finally { Pop-Location }
})

Write-Host ""
if ($ok) { Write-Host "ALL GREEN ✅"; exit 0 }
else { Write-Host "SOMETHING FAILED ❌"; exit 1 }
