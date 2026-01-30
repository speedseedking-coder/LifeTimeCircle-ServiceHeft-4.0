# Patch: entfernt DeprecationWarnings
# - FastAPI: ersetzt @app.on_event("startup") durch lifespan
# - Python: ersetzt datetime.utcnow() durch datetime.now(timezone.utc) (timezone-aware)
#
# Ausführen im server-Ordner:
#   pwsh -ExecutionPolicy Bypass -File .\scripts\patch_deprecations.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot

$mainPath = Join-Path $serverRoot "app\main.py"
$mcPath   = Join-Path $serverRoot "app\services\masterclipboard.py"

function Backup-File([string]$path) {
  if (Test-Path $path) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item $path "$path.bak.$ts" -Force
  }
}

# 1) main.py -> Lifespan (ersetzen auf kanonische Version)
if (Test-Path $mainPath) {
  Backup-File $mainPath

  $mainContent = @'
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.session import init_db
from app.routers.masterclipboard import router as masterclipboard_router
from app.auth.routes import router as auth_router


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # DB initialisieren (create_all – migrations folgen später)
        init_db()
        yield

    app = FastAPI(
        title="LifeTimeCircle – ServiceHeft 4.0",
        version="0.1.0",
        docs_url="/docs" if settings.env != "prod" else None,
        redoc_url="/redoc" if settings.env != "prod" else None,
        openapi_url="/openapi.json" if settings.env != "prod" else None,
        lifespan=lifespan,
    )

    # Router
    app.include_router(auth_router)
    app.include_router(masterclipboard_router)

    @app.get("/health", include_in_schema=False)
    def health() -> dict:
        return {"ok": True}

    # Minimaler Exception-Fallback (keine Payload-Logs)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        # Keine Details rausgeben (prod-sicher). In dev nur generisch.
        if settings.env == "dev":
            return JSONResponse(status_code=500, content={"error": "internal_error", "detail": str(exc)})
        return JSONResponse(status_code=500, content={"error": "internal_error"})

    return app


app = create_app()
'@

  Set-Content -Path $mainPath -Value $mainContent -Encoding UTF8
  Write-Host "OK: main.py -> lifespan umgestellt"
} else {
  Write-Host "SKIP: main.py nicht gefunden ($mainPath)"
}

# 2) masterclipboard.py -> datetime.utcnow() ersetzen
if (Test-Path $mcPath) {
  $raw = Get-Content -Path $mcPath -Raw -Encoding UTF8
  $orig = $raw

  # Ersetze utcnow Varianten
  $raw = $raw -replace 'datetime\.utcnow\(\)', 'datetime.now(timezone.utc)'
  $raw = $raw -replace 'datetime\.datetime\.utcnow\(\)', 'datetime.datetime.now(datetime.timezone.utc)'

  # Import fix: from datetime import ... -> timezone ergänzen
  if ($raw -match '(?m)^\s*from\s+datetime\s+import\s+([^\r\n]+)\s*$') {
    $raw = [regex]::Replace($raw, '(?m)^\s*from\s+datetime\s+import\s+([^\r\n]+)\s*$',
      {
        param($m)
        $imports = $m.Groups[1].Value.Trim()
        if ($imports -match '\btimezone\b') { return $m.Value }
        return "from datetime import $imports, timezone"
      }, 1)
  }

  if ($raw -ne $orig) {
    Backup-File $mcPath
    Set-Content -Path $mcPath -Value $raw -Encoding UTF8
    Write-Host "OK: masterclipboard.py -> utcnow() ersetzt + timezone import"
  } else {
    Write-Host "OK: masterclipboard.py unverändert (kein utcnow gefunden?)"
  }
} else {
  Write-Host "SKIP: masterclipboard.py nicht gefunden ($mcPath)"
}

Write-Host "FERTIG ✅"
