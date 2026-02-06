# server\scripts\patch_export_missing_tables.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Patch-MissingTableLineWise([string]$Text, [string]$Marker) {
  $lines = $Text -split "`r?`n"
  $changed = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match [regex]::Escape($Marker)) {
      $line = $lines[$i]

      # Detail auf not_found mappen
      $line = $line -replace "detail\s*=\s*'"+[regex]::Escape($Marker)+"'", "detail='not_found'"
      $line = $line -replace 'detail\s*=\s*"'+[regex]::Escape($Marker)+'"', 'detail="not_found"'
      $line = $line -replace "'"+[regex]::Escape($Marker)+"'", "'not_found'"
      $line = $line -replace '"'+[regex]::Escape($Marker)+'"', '"not_found"'

      # Status 500 -> 404 (nur in dieser Zeile)
      $line = $line -replace "status_code\s*=\s*500\b", "status_code=404"
      $line = $line -replace "status_code\s*=\s*status\.HTTP_500_INTERNAL_SERVER_ERROR\b", "status_code=status.HTTP_404_NOT_FOUND"
      $line = $line -replace "\(\s*500\s*,", "(404,"
      $line = $line -replace "\(\s*status\.HTTP_500_INTERNAL_SERVER_ERROR\s*,", "(status.HTTP_404_NOT_FOUND,"

      if ($line -ne $lines[$i]) {
        $lines[$i] = $line
        $changed = $true
      }
    }
  }

  return @{
    Text    = ($lines -join "`n")
    Changed = $changed
  }
}

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$targets = @(
  @{ Path = (Join-Path $serverRoot "app\routers\export_vehicle.py");    Marker = "vehicle_table_missing" },
  @{ Path = (Join-Path $serverRoot "app\routers\export_servicebook.py"); Marker = "servicebook_table_missing" }
)

$patched = @()

foreach ($t in $targets) {
  $path = [string]$t.Path
  if (-not (Test-Path $path)) {
    Write-Host "SKIP (nicht gefunden): $path"
    continue
  }

  $before = [System.IO.File]::ReadAllText($path)

  $res = Patch-MissingTableLineWise -Text $before -Marker ([string]$t.Marker)
  $after = [string]$res.Text

  if ($res.Changed -and ($after -ne $before)) {
    Write-Utf8NoBom -Path $path -Content $after
    $patched += $path
    Write-Host "OK gepatcht: $path"
  } else {
    Write-Host "OK unverändert (Marker nicht gefunden/kein Patch nötig): $path"
  }
}

if ($patched.Count -gt 0) {
  Write-Host ""
  Write-Host "FERTIG ✅ Gepatchte Dateien:"
  $patched | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Host ""
  Write-Host "HINWEIS: Nichts geändert (Marker evtl. anders benannt)."
}
