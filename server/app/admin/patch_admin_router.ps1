$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$mainPy = Join-Path $serverRoot "app\main.py"
$adminInit = Join-Path $serverRoot "app\admin\__init__.py"

if (!(Test-Path $mainPy)) {
  Write-Host "FEHLT: $mainPy" -ForegroundColor Red
  exit 1
}

# admin package sicherstellen
$adminDir = Split-Path -Parent $adminInit
if (!(Test-Path $adminDir)) { New-Item -ItemType Directory -Path $adminDir | Out-Null }
if (!(Test-Path $adminInit)) { Set-Content -Path $adminInit -Value "# admin package`n" -Encoding UTF8 }

$src = Get-Content -Path $mainPy -Raw -Encoding UTF8
$orig = $src

# 1) Import hinzufügen
if ($src -notmatch "from\s+app\.admin\.routes\s+import\s+router\s+as\s+admin_router") {
  if ($src -match "from\s+app\.auth\.routes\s+import\s+router\s+as\s+auth_router") {
    $src = $src -replace "from\s+app\.auth\.routes\s+import\s+router\s+as\s+auth_router",
      "from app.auth.routes import router as auth_router`r`nfrom app.admin.routes import router as admin_router"
    Write-Host "OK: admin_router import eingefuegt"
  } else {
    Write-Host "FEHLT: Konnte auth_router import nicht finden (main.py). Bitte manuell: from app.admin.routes import router as admin_router" -ForegroundColor Yellow
  }
} else {
  Write-Host "OK: admin_router import schon drin"
}

# 2) include_router(admin_router) nach auth_router include
if ($src -notmatch "include_router\(\s*admin_router\s*\)") {
  $pattern = '(?m)^(?<indent>\s*)app\.include_router\(\s*auth_router\s*\)\s*$'
  if ($src -match $pattern) {
    $src = [regex]::Replace($src, $pattern, {
      param($m)
      $indent = $m.Groups["indent"].Value
      return "$($indent)app.include_router(auth_router)`r`n$($indent)app.include_router(admin_router)"
    })
    Write-Host "OK: app.include_router(admin_router) eingefuegt"
  } else {
    Write-Host "FEHLT: Konnte app.include_router(auth_router) nicht finden (main.py). Bitte manuell include_router(admin_router) in create_app setzen." -ForegroundColor Yellow
  }
} else {
  Write-Host "OK: include_router(admin_router) schon drin"
}

if ($src -ne $orig) {
  Set-Content -Path $mainPy -Value $src -Encoding UTF8
  Write-Host "FERTIG: $mainPy gepatcht" -ForegroundColor Green
} else {
  Write-Host "NICHTS ZU TUN (main.py unveraendert)" -ForegroundColor Green
}
