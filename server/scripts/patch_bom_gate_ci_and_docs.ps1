param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8NoBom([string]$path) {
  $bytes = [System.IO.File]::ReadAllBytes($path)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $bytes = $bytes[3..($bytes.Length-1)]
  }
  $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
  return $utf8.GetString($bytes)
}

function Write-Utf8NoBom([string]$path, [string]$text) {
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $utf8)
}

function Ensure-Contains([string]$path, [string]$needle, [string]$blockToAppend) {
  $s = Read-Utf8NoBom $path
  if ($s -notmatch [regex]::Escape($needle)) {
    $s = $s.TrimEnd() + "`r`n" + $blockToAppend.Trim() + "`r`n"
    Write-Utf8NoBom $path $s
    Write-Host "UPDATED: $path (appended block)"
    return $true
  }
  Write-Host "OK: $path (already contains needle)"
  return $false
}

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root
[Environment]::CurrentDirectory = $root

$changed = $false

# --- 1) CI: add BOM gate step in job pytest ---
$ciPath = Join-Path $root ".github/workflows/ci.yml"
if (-not (Test-Path -LiteralPath $ciPath)) { throw "Missing: $ciPath" }
$ci = Read-Utf8NoBom $ciPath

if ($ci -notmatch "LTC BOM gate \(UTF-8 no BOM\)") {
  $pattern = '(?ms)(^\s*-\s*name:\s*Setup Python\s*\R\s*uses:\s*actions/setup-python@v5\s*\R\s*with:\s*\R\s*python-version:\s*"[0-9.]+"\s*\R)'
  if ($ci -notmatch $pattern) {
    throw "CI.yml: Konnte Setup-Python Step nicht finden (Pattern mismatch)."
  }

  $insert = @'
      - name: LTC BOM gate (UTF-8 no BOM)
        shell: bash
        working-directory: ${{ github.workspace }}
        run: python tools/bom_scan.py --root .

'@

  $ci2 = [regex]::Replace($ci, $pattern, "`$1`r`n$insert", 1)
  Write-Utf8NoBom $ciPath $ci2
  Write-Host "UPDATED: .github/workflows/ci.yml (inserted BOM gate step)"
  $changed = $true
} else {
  Write-Host "OK: .github/workflows/ci.yml (BOM gate step already present)"
}

# --- 2) docs/06_WORK_RULES.md ---
$wrPath = Join-Path $root "docs/06_WORK_RULES.md"
if (-not (Test-Path -LiteralPath $wrPath)) { throw "Missing: $wrPath" }
$wr = Read-Utf8NoBom $wrPath

$old = @"
- UTF-8 only
- Kein BOM
- Mojibake-Fixes nur auf gemeldete Stellen
- Scanner SoT: tools/mojibake_scan.js
"@

$new = @"
- UTF-8 only
- Kein BOM (UTF-8 no-BOM ist verbindlich)
- BOM-Scanner SoT: tools/bom_scan.py
- BOM-Gate enforced in tools/test_all.ps1 + .github/workflows/ci.yml (Job `pytest`) + tools/ist_check.ps1
- Mojibake-Fixes nur auf gemeldete Stellen
- Scanner SoT: tools/mojibake_scan.js
"@

if ($wr -like "*$old*") {
  $wr2 = $wr.Replace($old, $new)
  Write-Utf8NoBom $wrPath $wr2
  Write-Host "UPDATED: docs/06_WORK_RULES.md (encoding bullets updated)"
  $changed = $true
} elseif ($wr -notmatch "tools/bom_scan\.py") {
  # fallback: append a small note (keine Duplikate)
  $append = @"
---
### BOM Gate (UTF-8 no-BOM)
- BOM-Scanner SoT: tools/bom_scan.py
- enforced in tools/test_all.ps1 + .github/workflows/ci.yml (Job `pytest`) + tools/ist_check.ps1
"@
  $wr2 = $wr.TrimEnd() + "`r`n`r`n" + $append.Trim() + "`r`n"
  Write-Utf8NoBom $wrPath $wr2
  Write-Host "UPDATED: docs/06_WORK_RULES.md (appended BOM section)"
  $changed = $true
} else {
  Write-Host "OK: docs/06_WORK_RULES.md (BOM content already present)"
}

# --- 3) docs/01_DECISIONS.md: add D-035 ---
$decPath = Join-Path $root "docs/01_DECISIONS.md"
if (-not (Test-Path -LiteralPath $decPath)) { throw "Missing: $decPath" }
$decNeedle = "## D-035: UTF-8 no-BOM Gate ist verpflichtend"
$decBlock = @"
---

## D-035: UTF-8 no-BOM Gate ist verpflichtend (lokal + CI + IST-Check)
**Status:** beschlossen  
**Datum:** 2026-02-24  
**Warum:** UTF-8 BOM (EF BB BF) verursacht Signal-Drift bei Scannern/Tooling und fuehrt zu nicht-deterministischen Ergebnissen. Das muss fail-fast und einheitlich verhindert werden.  
**Konsequenz:**  
- Source-of-Truth fuer BOM-Pruefung: `tools/bom_scan.py`.  
- `tools/test_all.ps1` bricht hart ab, wenn BOM gefunden wird.  
- CI Job **`pytest`** enthaelt den Step **"LTC BOM gate (UTF-8 no BOM)"** vor pytest.  
- `tools/ist_check.ps1` fuehrt `bom_scan` aus und erzwingt Exit-Code (kein Drift).  
- BOM-Entfernung erfolgt nur als Byte-Prefix-Strip `EF BB BF` (kein Content-Change).  
"@
if (Ensure-Contains $decPath $decNeedle $decBlock) { $changed = $true }

# --- 4) docs/99_MASTER_CHECKPOINT.md: add WIP entry ---
$mcPath = Join-Path $root "docs/99_MASTER_CHECKPOINT.md"
if (-not (Test-Path -LiteralPath $mcPath)) { throw "Missing: $mcPath" }
$mc = Read-Utf8NoBom $mcPath
$mcNeedle = "### WIP: UTF-8 no-BOM Gate enforced (P0)"
if ($mc -notmatch [regex]::Escape($mcNeedle)) {
  $hdr = "## WIP / Offene PRs / Branch-Stand (nicht main)"
  if ($mc -notmatch [regex]::Escape($hdr)) { throw "MASTER_CHECKPOINT: WIP header not found." }

  $wipBlock = @"
### WIP: UTF-8 no-BOM Gate enforced (P0)
- Status: **PR in Arbeit** (Branch: `feat/bom-gate`)
- Scope:
  - neues Tool: `tools/bom_scan.py` (Exit 1 bei BOM)
  - Gate lokal: `tools/test_all.ps1` (fail-fast)
  - Gate CI: `.github/workflows/ci.yml` Job `pytest` Step "LTC BOM gate (UTF-8 no BOM)"
  - Gate IST: `tools/ist_check.ps1` erzwingt `bom_scan` Exit-Code
  - Cleanup: BOM nur als Prefix `EF BB BF` entfernt (byte-level)
- Evidence lokal:
  - `python tools/bom_scan.py --root .` → OK
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1` → ALL GREEN
"@

  $mc2 = $mc.Replace($hdr, $hdr + "`r`n`r`n" + $wipBlock.Trim() + "`r`n")
  Write-Utf8NoBom $mcPath $mc2
  Write-Host "UPDATED: docs/99_MASTER_CHECKPOINT.md (added WIP entry)"
  $changed = $true
} else {
  Write-Host "OK: docs/99_MASTER_CHECKPOINT.md (WIP entry already present)"
}

Write-Host ""
if ($changed) {
  Write-Host "DONE: Patch applied. Next: python tools/bom_scan.py --root . ; pwsh tools/test_all.ps1 ; commit+push"
} else {
  Write-Host "DONE: No changes needed."
}