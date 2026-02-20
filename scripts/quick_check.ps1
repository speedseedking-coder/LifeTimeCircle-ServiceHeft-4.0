# Quick checks used by repo scripts (PowerShell 5.1 compatible)
$ErrorActionPreference = "Stop"

# Add/adjust patterns as needed
$checks = @(
  @{ name = "Trust-Ampel bewertet ausschließlich"; pattern = '(?i)Trust-Ampel\s+bewertet\s+ausschlie(ß|ss|ÃŸ|ÃY)lich' },
  @{ name = "keine Kennzahlen/Counts/Prozente/Zeiträume"; pattern = '(?i)keine\s+Kennzahlen.*Counts.*Prozente.*Zeitr(ä|ae|Ã¤)ume' }
)

$files = Get-ChildItem -Recurse -File -Path "." -Include *.md,*.ts,*.tsx,*.js,*.jsx,*.py,*.ps1,*.json,*.yml,*.yaml,*.txt -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\node_modules\\|\\dist\\|\\.git\\|\\.pytest_cache\\|\\test-results\\' }

$any = $false

foreach ($c in $checks) {
  $hits = @()
  foreach ($f in $files) {
    try {
      $m = Select-String -Path $f.FullName -Pattern $c.pattern -SimpleMatch:$false -AllMatches -ErrorAction Stop
      if ($m) { $hits += $m }
    } catch {
      # ignore unreadable/binary/etc
    }
  }

  if ($hits.Count -gt 0) {
    $any = $true
    Write-Host ("FAIL: {0} (max 50 Treffer):" -f $c.name) -ForegroundColor Red
    $hits | Select-Object -First 50 | ForEach-Object {
      $line = ""
      if ($null -ne $_.Line) { $line = ($_.Line.ToString()).Trim() }
      Write-Host (" - {0}:{1}:{2}" -f $_.Path, $_.LineNumber, $line)
    }
    if ($hits.Count -gt 50) { Write-Host (" - ... {0} weitere Treffer" -f ($hits.Count - 50)) }
  } else {
    Write-Host ("OK: {0}" -f $c.name) -ForegroundColor Green
  }
}

if ($any) { exit 1 } else { exit 0 }