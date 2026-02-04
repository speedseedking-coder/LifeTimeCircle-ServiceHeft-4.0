
param(
  [string]$MainFile = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ServerDir = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $MainFile -or $MainFile.Trim().Length -eq 0) {
  $MainFile = Join-Path $ServerDir "app\main.py"
}

if (-not (Test-Path $MainFile)) { throw "main.py nicht gefunden: $MainFile" }

$content = Get-Content -Path $MainFile -Raw

# 1) Import sicherstellen (ohne Einrückung)
$importLine = "from app.routers import servicebook"
if ($content -notmatch [regex]::Escape($importLine)) {
  $lines = $content -split "`r?`n"
  $insertAt = 0
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^(import|from)\s+") { $insertAt = $i + 1 } else { break }
  }
  $new = @()
  if ($insertAt -gt 0) { $new += $lines[0..($insertAt-1)] }
  $new += $importLine
  $new += $lines[$insertAt..($lines.Length-1)]
  $content = ($new -join "`r`n")
}

# 2) include_router IN create_app() vor return app einfügen (korrekte Einrückung)
$includeLine = "app.include_router(servicebook.router)"
if ($content -notmatch [regex]::Escape($includeLine)) {

  $lines = $content -split "`r?`n"

  $createIdx = -1
  $returnIdx = -1
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^\s*def\s+create_app\s*\(") { $createIdx = $i; continue }
    if ($createIdx -ge 0 -and $lines[$i] -match "^\s*return\s+app\s*$") { $returnIdx = $i; break }
  }
  if ($createIdx -lt 0 -or $returnIdx -lt 0) {
    throw "Konnte create_app()/return app nicht finden. Bitte main.py prüfen."
  }

  $indent = ""
  if ($lines[$returnIdx] -match "^(\s*)return\s+app\s*$") {
    $indent = $Matches[1]
  }

  $out = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($i -eq $returnIdx) {
      $out.Add($indent + $includeLine)
    }
    $out.Add($lines[$i])
  }

  $content = ($out -join "`r`n")
}

Set-Content -Path $MainFile -Value $content -Encoding UTF8
Write-Host "OK: servicebook router sicher in create_app() inkludiert:"
Write-Host "  $MainFile"
