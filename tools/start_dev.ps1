# tools/start_dev.ps1
# LifeTimeCircle – Service Heft 4.0
# Startet API + WEB in Windows Terminal Tabs (oder fallback pwsh) inkl. Healthcheck und optional Browser-Open.
# Secrets werden niemals ausgegeben (nur Länge).
#
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1 -ApiOnly
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1 -WebOnly -NoInstall
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1 -NoWt
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\start_dev.ps1 -Open

[CmdletBinding()]
param(
  [switch]$ApiOnly,
  [switch]$WebOnly,
  [switch]$NoInstall,
  [switch]$NoWt,
  [switch]$Open
)

$ErrorActionPreference = "Stop"

function RepoRoot {
  $root = (& git rev-parse --show-toplevel 2>$null).Trim()
  if (-not $root) { throw "STOP: Repo-Root nicht gefunden (git rev-parse --show-toplevel fehlgeschlagen)." }
  return $root
}

function Enc([string]$s) {
  # PowerShell EncodedCommand erwartet UTF-16LE ("Unicode")
  [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($s))
}

function CurlJsonOk([string]$url) {
  try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
    return ($resp.StatusCode -eq 200)
  } catch { return $false }
}

$root = RepoRoot
Set-Location $root

# Safety: Secret vorhanden (niemals ausgeben)
if ([string]::IsNullOrWhiteSpace($env:LTC_SECRET_KEY) -or $env:LTC_SECRET_KEY.Length -lt 16) {
  throw "STOP: LTC_SECRET_KEY fehlt/zu kurz (>=16). Setze ihn und starte erneut."
}
$klen = $env:LTC_SECRET_KEY.Length

$apiDir = Join-Path $root "server"
$webDir = Join-Path $root "packages\web"

$apiUrl = "http://127.0.0.1:8000"
$healthUrl = "$apiUrl/health"
$webUrl = "http://127.0.0.1:5173"

$apiScript = @"
Set-Location '$apiDir'
Write-Host 'LTC_SECRET_KEY len=$klen'
poetry run uvicorn app.main:app --reload
"@

$webScript = @"
Set-Location '$webDir'
"@ + ($(if ($NoInstall) { "" } else { "npm install`n" })) + @"
npm run dev
"@

$apiEnc = Enc $apiScript
$webEnc = Enc $webScript

$useWt = (-not $NoWt) -and (Get-Command wt -ErrorAction SilentlyContinue)

# Start
if (-not $WebOnly) {
  if ($useWt) { wt new-tab --title "LTC API" -d "$apiDir" pwsh -NoProfile -NoExit -EncodedCommand $apiEnc | Out-Null }
  else { Start-Process pwsh -ArgumentList @("-NoProfile","-NoExit","-EncodedCommand",$apiEnc) | Out-Null }
}

if (-not $ApiOnly) {
  if ($useWt) { wt new-tab --title "LTC WEB" -d "$webDir" pwsh -NoProfile -NoExit -EncodedCommand $webEnc | Out-Null }
  else { Start-Process pwsh -ArgumentList @("-NoProfile","-NoExit","-EncodedCommand",$webEnc) | Out-Null }
}

# Healthcheck (best-effort, wartet kurz)
if (-not $WebOnly) {
  $ok = $false
  for ($i=0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 300
    if (CurlJsonOk $healthUrl) { $ok = $true; break }
  }
  if ($ok) { Write-Host "API OK: $healthUrl" }
  else { Write-Host "API WARN: Healthcheck nicht bestätigt (URL: $healthUrl)" }
}

Write-Host "API: $apiUrl"
Write-Host "WEB: $webUrl"

if ($Open) {
  Start-Process $webUrl | Out-Null
  Start-Process "$apiUrl/docs" | Out-Null
  Start-Process "$apiUrl/redoc" | Out-Null
}