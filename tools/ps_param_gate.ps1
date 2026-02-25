param(
  [string[]]$Paths = @("tools/pr_done.ps1")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-FirstSignificantLine {
  param([string[]]$Lines)

  for ($i = 0; $i -lt $Lines.Count; $i++) {
    $t = $Lines[$i].Trim()
    if ($t -eq "") { continue }

    # allowed before param:
    if ($t -match '^(?i)#\s*requires\b') { continue }
    if ($t -match '^(?i)using\s+') { continue }
    if ($t -match '^\s*#') { continue } # comments
    if ($t -match '^\s*\[(?i)(cmdletbinding|outputtype|diagnostics\.codeanalysis\.suppressmessage)\b') { continue }

    return @{ Index = $i; Text = $Lines[$i] }
  }
  return $null
}

function Assert-ParamAtTop {
  param([string]$Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing file: $Path"
  }

  $lines = Get-Content -LiteralPath $Path -Encoding UTF8
  $first = Get-FirstSignificantLine -Lines $lines

  if ($null -eq $first) {
    throw "File is empty: $Path"
  }

  if ($first.Text.TrimStart() -notmatch '^(?i)param\s*\(') {
    throw "param(...) must be the first significant statement (after comments/#requires/using/attributes). Found: '$($first.Text.Trim())' (line $($first.Index + 1))"
  }
}

Write-Host ""
Write-Host "==> PowerShell param gate" -ForegroundColor Cyan

foreach ($p in $Paths) {
  Assert-ParamAtTop -Path $p
  Write-Host "OK: $p" -ForegroundColor Green
}
