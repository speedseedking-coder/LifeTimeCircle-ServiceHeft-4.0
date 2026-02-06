# server/scripts/fix_main_py_public_site_indent.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$mainPath = Join-Path $repo "server/app/main.py"

if (!(Test-Path $mainPath)) { Fail "Missing file: $mainPath" }

$lines = Get-Content -Encoding UTF8 $mainPath

# Indent aus EXISTIERENDEN include_router(...) Zeilen ableiten (ohne public_site_router)
$indent = ""
$baseMatches = $lines | Select-String -Pattern '^(?<indent>\s*)app\.include_router\(\s*(?!public_site_router\b)' -AllMatches
if ($baseMatches) {
  $indent = $baseMatches[0].Matches[0].Groups["indent"].Value
} else {
  # Fallback: wenn keine anderen include_router gefunden werden (ungewöhnlich)
  $indent = "    "
}

$patternPublic = '^\s*app\.include_router\(\s*public_site_router\s*\)\s*$'
$changed = $false

for ($i = 0; $i -lt $lines.Length; $i++) {
  if ($lines[$i] -match $patternPublic) {
    $lines[$i] = ($indent + "app.include_router(public_site_router)")
    $changed = $true
  }
}

if (-not $changed) {
  Fail "Did not find 'app.include_router(public_site_router)' in $mainPath. (Patch_add_public_site may not have been applied or line differs.)"
}

$lines | Set-Content -Encoding UTF8 $mainPath

Write-Host "OK: fixed indentation for app.include_router(public_site_router) in server/app/main.py" -ForegroundColor Green
Write-Host "Next: start uvicorn again." -ForegroundColor Green