# Startet die API lokal (Windows PowerShell)
# Voraussetzung: poetry install
# Env vars:
#   LTC_SECRET_KEY (Pflicht)
#   LTC_DATABASE_URL (optional)

$env:LTC_ENV = "dev"

if (-not $env:LTC_SECRET_KEY) {
  Write-Host "FEHLT: LTC_SECRET_KEY (Pflicht). Beispiel: `$env:LTC_SECRET_KEY = 'dev-only-change-me'`" -ForegroundColor Red
  exit 1
}

poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
