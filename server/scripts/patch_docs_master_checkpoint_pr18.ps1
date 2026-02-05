param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $target)) {
  throw "Target not found: $target"
}

$text = Get-Content -Raw -Encoding UTF8 $target

# Insert Bullet in "Status (Hauptmodul zuerst)"
$needleStatus = "## Status (Hauptmodul zuerst)"
if ($text -notmatch [regex]::Escape("RBAC Guard-Coverage Test")) {
  if ($text -match [regex]::Escape($needleStatus)) {
    # Add bullet after Branch Protection line (robust: insert after the line containing "Branch Protection")
    if ($text -match "(?m)^\s*✅\s*Branch Protection.+\r?\n") {
      $text = [regex]::Replace(
        $text,
        "(?m)^(?<line>\s*✅\s*Branch Protection.+\r?\n)",
        '${line}✅ RBAC Guard-Coverage Test: deny-by-default enforced (PR #18)`r`n',
        1
      )
    } else {
      # fallback: insert directly under the status header
      $text = [regex]::Replace(
        $text,
        "(?m)^##\s*Status\s*\(Hauptmodul zuerst\)\s*\r?\n",
        "## Status (Hauptmodul zuerst)`r`n✅ RBAC Guard-Coverage Test: deny-by-default enforced (PR #18)`r`n",
        1
      )
    }
  } else {
    throw "Konnte Abschnitt '$needleStatus' nicht finden."
  }
}

# Insert detail in Servicebook section (idempotent)
$detailLine = "✅ Guard-Coverage: server/tests/test_rbac_guard_coverage.py; /consent Router mit Depends(forbid_moderator) (PR #18)"
if ($text -notmatch [regex]::Escape($detailLine)) {
  if ($text -match "(?m)^##\s*Servicebook\s*\(Core\s*/\s*System of Record\)\s*\r?\n") {
    $text = [regex]::Replace(
      $text,
      "(?m)^(##\s*Servicebook\s*\(Core\s*/\s*System of Record\)\s*\r?\n)",
      "`$1$detailLine`r`n",
      1
    )
  }
}

# ensure EOF newline
if (-not $text.EndsWith("`n")) { $text += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $text
Write-Host "OK: patched $target (added PR #18 notes)"