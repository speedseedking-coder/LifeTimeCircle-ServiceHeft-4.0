# server/scripts/patch_root_redirect_to_public_site.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Content
  )
  if (-not $Content.EndsWith("`n")) { $Content += "`n" }
  Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
}

function Get-NewLine {
  param([Parameter(Mandatory=$true)][string]$Text)
  if ($Text.Contains("`r`n")) { return "`r`n" }
  return "`n"
}

function Ensure-FastapiResponsesImport {
  param(
    [Parameter(Mandatory=$true)][string]$Content,
    [Parameter(Mandatory=$true)][string]$NL
  )

  $pattern = '(?m)^(from\s+fastapi\.responses\s+import\s+)(.+)$'
  $m = [regex]::Match($Content, $pattern)

  if ($m.Success) {
    $prefix  = $m.Groups[1].Value
    $imports = $m.Groups[2].Value.Trim()

    $needRedirect = ($imports -notmatch '\bRedirectResponse\b')
    $needResponse = ($imports -notmatch '\bResponse\b')

    if (-not $needRedirect -and -not $needResponse) { return $Content }

    $newImports = $imports
    if ($needRedirect) { $newImports += ", RedirectResponse" }
    if ($needResponse) { $newImports += ", Response" }

    return $Content.Replace($m.Value, ($prefix + $newImports))
  }

  $insert = "from fastapi.responses import RedirectResponse, Response$NL"

  $m2 = [regex]::Match($Content, '(?m)^(from\s+fastapi[^\r\n]*\r?\n)')
  if ($m2.Success) {
    $idx = $m2.Index + $m2.Length
    return $Content.Substring(0, $idx) + $insert + $Content.Substring($idx)
  }

  return $insert + $Content
}

function Remove-RootRedirectBlocks {
  param([Parameter(Mandatory=$true)][string]$Content)

  # Marker block entfernen (egal wo er steht)
  $markerPattern = '(?ms)^\s*#\s*LTC-AUTO:\s*root-redirect\s*begin\s*\r?\n.*?^\s*#\s*LTC-AUTO:\s*root-redirect\s*end\s*\r?\n?'
  $Content = [regex]::Replace($Content, $markerPattern, "", [System.Text.RegularExpressions.RegexOptions]::Multiline)

  # Root-Route (ohne Marker) entfernen
  $rootPattern = '(?ms)^\s*@app\.get\(\s*["'']\/["'']\s*,\s*include_in_schema\s*=\s*False\s*\)\s*\r?\n\s*def\s+root\s*\(\s*\)\s*:\s*\r?\n\s*return\s+RedirectResponse\s*\(\s*url\s*=\s*["'']\/public\/site["'']\s*\)\s*\r?\n\s*\r?\n?'
  $Content = [regex]::Replace($Content, $rootPattern, "", [System.Text.RegularExpressions.RegexOptions]::Multiline)

  # Favicon-Route (ohne Marker) entfernen
  $favPattern = '(?ms)^\s*@app\.get\(\s*["'']\/favicon\.ico["'']\s*,\s*include_in_schema\s*=\s*False\s*\)\s*\r?\n\s*def\s+favicon\s*\(\s*\)\s*:\s*\r?\n\s*return\s+Response\s*\(\s*status_code\s*=\s*204\s*\)\s*\r?\n\s*\r?\n?'
  $Content = [regex]::Replace($Content, $favPattern, "", [System.Text.RegularExpressions.RegexOptions]::Multiline)

  return $Content
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..") | Select-Object -ExpandProperty Path

$mainPath = Join-Path $repoRoot "server\app\main.py"
if (-not (Test-Path -LiteralPath $mainPath)) { throw "FAIL: not found: $mainPath" }

$content = Get-Content -LiteralPath $mainPath -Raw
$NL = Get-NewLine -Text $content

# 1) Alte/kaputte Blocks IMMER raus
$content = Remove-RootRedirectBlocks -Content $content

# 2) Imports sicherstellen
$content = Ensure-FastapiResponsesImport -Content $content -NL $NL

# 3) Guard: app muss irgendwo im File definiert werden, sonst keine Route hinzufügen
if ($content -notmatch '(?m)^\s*app\s*(?::[^=]+)?\s*=\s*') {
  throw "FAIL: In server/app/main.py wurde keine app-Zuweisung gefunden (app = ...)."
}

# 4) Block IMMER am Dateiende anhängen (sicher nach app-Definition)
$block = @(
  ""
  "# LTC-AUTO: root-redirect begin"
  '@app.get("/", include_in_schema=False)'
  "def root():"
  '    return RedirectResponse(url="/public/site")'
  ""
  '@app.get("/favicon.ico", include_in_schema=False)'
  "def favicon():"
  "    return Response(status_code=204)"
  "# LTC-AUTO: root-redirect end"
  ""
) -join $NL

# Falls Marker doch vorhanden (sollte nach Remove nicht), dann nicht doppeln
if ($content -match '#\s*LTC-AUTO:\s*root-redirect\s*begin') {
  Write-Utf8NoBom -Path $mainPath -Content $content
  Write-Host "OK: root redirect marker already present (no-op)."
  exit 0
}

if (-not $content.EndsWith($NL)) { $content += $NL }
$content += $block

Write-Utf8NoBom -Path $mainPath -Content $content
Write-Host "OK: Root redirect appended at EOF in server/app/main.py (after app definition)."
Write-Host "NEXT: Restart uvicorn."