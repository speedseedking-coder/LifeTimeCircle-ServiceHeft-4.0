# server/scripts/patch_include_servicebook_router.ps1
param(
  [string]$MainFile = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Script liegt in server\scripts\...
$ServerDir = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $MainFile -or $MainFile.Trim().Length -eq 0) {
  $MainFile = Join-Path $ServerDir "app\main.py"
}

if (-not (Test-Path $MainFile)) {
  throw "main.py nicht gefunden: $MainFile"
}

$content = Get-Content -Path $MainFile -Raw

# 1) Import sicherstellen: from app.routers import servicebook
$importLine = "from app.routers import servicebook"
if ($content -notmatch [regex]::Escape($importLine)) {
  # Einfügepunkt: nach anderen router-imports oder nach bestehenden from app.routers import ...
  if ($content -match "from app\.routers import[^\r\n]*\r?\n") {
    # Insert after first matching import block line
    $content = [regex]::Replace(
      $content,
      "from app\.routers import[^\r\n]*\r?\n",
      { param($m) $m.Value + $importLine + "`r`n" },
      1
    )
  } else {
    # Fallback: ganz oben nach anderen Imports
    $lines = $content -split "`r?`n"
    $idx = 0
    for ($i=0; $i -lt $lines.Length; $i++) {
      if ($lines[$i] -match "^(import|from)\s+") { $idx = $i + 1 } else { break }
    }
    $new = @()
    $new += $lines[0..($idx-1)]
    $new += $importLine
    $new += $lines[$idx..($lines.Length-1)]
    $content = ($new -join "`r`n")
  }
}

# 2) include_router sicherstellen
$includeLine = "app.include_router(servicebook.router)"
if ($content -notmatch [regex]::Escape($includeLine)) {
  # Insert near other include_router calls if present
  if ($content -match "app\.include_router\([^\)]*\)\r?\n") {
    $content = [regex]::Replace(
      $content,
      "app\.include_router\([^\)]*\)\r?\n",
      { param($m) $m.Value + $includeLine + "`r`n" },
      1
    )
  } else {
    # Fallback: append at end
    if (-not $content.EndsWith("`r`n")) { $content += "`r`n" }
    $content += "`r`n" + $includeLine + "`r`n"
  }
}

Set-Content -Path $MainFile -Value $content -Encoding UTF8
Write-Host "OK: servicebook router in main.py sichergestellt:"
Write-Host "  $MainFile"
