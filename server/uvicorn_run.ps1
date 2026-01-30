param(
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Immer im server-Ordner ausführen
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Pflicht: SECRET KEY (mind. 32 Zeichen)
if (-not $env:LTC_SECRET_KEY -or $env:LTC_SECRET_KEY.Trim().Length -lt 32) {
  Write-Host 'FEHLT: LTC_SECRET_KEY (Pflicht, mind. 32 Zeichen). Beispiel: $env:LTC_SECRET_KEY="dev-only-change-me-please-change-me-32chars-XXXX";'
  exit 1
}

# Default DB Path, falls nicht gesetzt
if (-not $env:LTC_DB_PATH -or $env:LTC_DB_PATH.Trim().Length -eq 0) {
  $env:LTC_DB_PATH = ".\data\app.db"
}

Write-Host ("Starte Uvicorn: http://{0}:{1}" -f $HostAddress, $Port)
Write-Host ("DB: {0}" -f $env:LTC_DB_PATH)

if ($env:LTC_DEV_EXPOSE_OTP) {
  Write-Host ("DEV OTP: {0}" -f $env:LTC_DEV_EXPOSE_OTP)
}

poetry run uvicorn app.main:app --reload --host $HostAddress --port $Port

