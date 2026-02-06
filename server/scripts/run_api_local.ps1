# server/scripts/run_api_local.ps1
param(
  [string]$HostAddr = "127.0.0.1",
  [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:LTC_SECRET_KEY) -or $env:LTC_SECRET_KEY.Length -lt 16) {
  throw "LTC_SECRET_KEY fehlt/zu kurz (>=16). DEV: `$env:LTC_SECRET_KEY='dev_test_secret_key_32_chars_minimum__OK'"
}

$serverDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $serverDir

poetry run uvicorn app.main:app --host $HostAddr --port $Port --reload