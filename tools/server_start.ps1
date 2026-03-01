[CmdletBinding()]
param(
  [string]$HostAddr = "127.0.0.1",
  [int]$Port = 8000,
  [switch]$NoReload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  $gitRoot = (& git rev-parse --show-toplevel 2>$null)
  if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($gitRoot)) {
    return $gitRoot.Trim()
  }

  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$repoRoot = Get-RepoRoot
$serverDir = Join-Path $repoRoot "server"

if (-not (Test-Path $serverDir)) {
  throw "Server-Verzeichnis nicht gefunden: $serverDir"
}

# Dokumentierter Schnellstart soll ohne manuelles Secret-Setzen funktionieren.
if ([string]::IsNullOrWhiteSpace($env:LTC_SECRET_KEY) -or $env:LTC_SECRET_KEY.Trim().Length -lt 16) {
  $env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
}

if ([string]::IsNullOrWhiteSpace($env:LTC_ENV)) {
  $env:LTC_ENV = "dev"
}

$uvicornArgs = @("app.main:app", "--host", $HostAddr, "--port", "$Port")
if (-not $NoReload) {
  $uvicornArgs += "--reload"
}

Write-Host ("Repo: {0}" -f $repoRoot)
Write-Host ("Server: {0}" -f $serverDir)
Write-Host ("LTC_ENV={0}" -f $env:LTC_ENV)
Write-Host ("LTC_SECRET_KEY len={0}" -f $env:LTC_SECRET_KEY.Length)
Write-Host ("Starte API: http://{0}:{1}" -f $HostAddr, $Port)

Push-Location $serverDir
try {
  & poetry run uvicorn @uvicornArgs
}
finally {
  Pop-Location
}
