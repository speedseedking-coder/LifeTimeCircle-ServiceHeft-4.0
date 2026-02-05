param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $target)) {
  throw "Target not found: $target"
}

$text = Get-Content -Raw -Encoding UTF8 $target

# Safety: falls ein früherer Lauf literal `r`n eingebaut hat
$text = $text.Replace('`r`n', '')

# --- Status Bullet einmalig einfügen ---
$statusBullet = "✅ RBAC Guard-Coverage Test: deny-by-default enforced (PR #18)"
if ($text -notmatch [regex]::Escape($statusBullet)) {
  $pat = "(?m)^(?<line>\s*✅\s*Branch Protection.+\r?\n)"
  $rx  = [regex]::new($pat, [System.Text.RegularExpressions.RegexOptions]::Multiline)

  if ($rx.IsMatch($text)) {
    $replacement = '${line}' + $statusBullet + "`r`n"
    $text = $rx.Replace($text, $replacement, 1)
  } else {
    $needle = "## Status (Hauptmodul zuerst)"
    if ($text -notmatch [regex]::Escape($needle)) {
      throw "Konnte Abschnitt '$needle' nicht finden."
    }
    $rx2 = [regex]::new("(?m)^##\s*Status\s*\(Hauptmodul zuerst\)\s*\r?\n", [System.Text.RegularExpressions.RegexOptions]::Multiline)
    $text = $rx2.Replace($text, "## Status (Hauptmodul zuerst)`r`n$statusBullet`r`n", 1)
  }
}

# --- Servicebook Detail einmalig (nur nach erstem Header) ---
$detailLine = "✅ Guard-Coverage: server/tests/test_rbac_guard_coverage.py; /consent Router mit Depends(forbid_moderator) (PR #18)"
if ($text -notmatch [regex]::Escape($detailLine)) {
  $pat3 = "(?m)^(##\s*Servicebook\s*\(Core\s*/\s*System of Record\)\s*\r?\n)"
  $rx3  = [regex]::new($pat3, [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if ($rx3.IsMatch($text)) {
    $replacement3 = '$1' + $detailLine + "`r`n"
    $text = $rx3.Replace($text, $replacement3, 1)
  }
}

# EOF newline
if (-not $text.EndsWith("`n")) { $text += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $text
Write-Host "OK: patched $target (PR #18 notes, no literal `r`n, single insert)"