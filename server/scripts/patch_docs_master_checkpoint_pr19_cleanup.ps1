param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $target)) { throw "Target not found: $target" }

$detailLine = "✅ Guard-Coverage: server/tests/test_rbac_guard_coverage.py; /consent Router mit Depends(forbid_moderator) (PR #18)"
$headerLine = "## Servicebook (Core / System of Record)"

$text = Get-Content -Raw -Encoding UTF8 $target

# 1) literal `r`n entfernen (das sind echte Backtick-Zeichen im Text)
$text = $text.Replace('`r`n', '')

# 2) alle bisherigen Detail-Lines entfernen (wir fügen gleich exakt 1x an definierter Stelle ein)
$lines = $text -split "(`r`n|`n|`r)"
$lines = $lines | Where-Object { $_ -ne $detailLine }

# 3) Detail-Line direkt nach dem ersten Servicebook-Header einfügen (falls vorhanden)
$idx = [Array]::IndexOf($lines, $headerLine)
if ($idx -ge 0) {
  $newLines = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    $newLines += $lines[$i]
    if ($i -eq $idx) { $newLines += $detailLine }
  }
  $lines = $newLines
} else {
  # Fallback: oben nach dem ersten '---' oder ans Ende
  $lines += ""
  $lines += $detailLine
}

# 4) zurückschreiben (CRLF) + EOF newline
$out = ($lines -join "`r`n")
if (-not $out.EndsWith("`r`n")) { $out += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $out
Write-Host "OK: cleaned $target (removed literal `r`n + re-inserted detail line once)"
