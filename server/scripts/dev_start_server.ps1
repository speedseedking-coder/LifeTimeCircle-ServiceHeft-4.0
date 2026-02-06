Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Muss im server-Ordner laufen
if (-not (Test-Path (Join-Path (Get-Location) "pyproject.toml"))) {
  throw "Bitte im server-Ordner ausführen (pyproject.toml nicht gefunden): $(Get-Location)"
}

# ENV (DEV)
$env:LTC_SECRET_KEY     = "dev-only-change-me-32-chars-minimum-OK!!"
$env:LTC_DEV_EXPOSE_OTP = "1"
$env:LTC_MAILER_MODE    = "null"
# optional:
# $env:LTC_DB_PATH      = ".\data\app.db"

# optional: Port 8000 freimachen
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

# fail-fast Syntax-Check
poetry run python -m py_compile .\app\main.py | Out-Null

# Start
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
