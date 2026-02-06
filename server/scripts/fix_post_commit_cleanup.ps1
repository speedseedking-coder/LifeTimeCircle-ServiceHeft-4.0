Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8PreserveBom([string]$path) {
  $bytes = [System.IO.File]::ReadAllBytes($path)
  $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  $start = if ($hasBom) { 3 } else { 0 }
  $text = [System.Text.Encoding]::UTF8.GetString($bytes, $start, $bytes.Length - $start)
  return @{ text = $text; hasBom = $hasBom }
}

function Write-Utf8PreserveBom([string]$path, [string]$text, [bool]$hasBom) {
  $enc = New-Object System.Text.UTF8Encoding($hasBom)
  [System.IO.File]::WriteAllText($path, $text, $enc)
}

function Ensure-Trailing-Newline([string]$text) {
  if ($text.Length -eq 0) { return "`n" }
  if ($text.EndsWith("`n")) { return $text }
  return ($text + "`n")
}

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

# --- 1) app/guards.py: get_current_user Import korrigieren ---
$guardsPath = Join-Path $serverRoot "app\guards.py"
if (Test-Path $guardsPath) {
  $r = Read-Utf8PreserveBom $guardsPath
  $orig = [string]$r.text
  $hasBom = [bool]$r.hasBom

  $new = $orig

  # häufigster Fehler: app.deps statt app.rbac
  $new = $new -replace '(?m)^\s*from\s+app\.deps\s+import\s+get_current_user\s*$', 'from app.rbac import get_current_user'

  if ($new -ne $orig) {
    Write-Utf8PreserveBom $guardsPath $new $hasBom
    Ok "guards.py: get_current_user Import auf app.rbac korrigiert"
  } else {
    Ok "guards.py: keine Änderung nötig"
  }
} else {
  Warn "guards.py nicht gefunden: $guardsPath"
}

# --- 2) app/admin/routes.py: doppeltes __future__ entfernen + Depends sicherstellen wenn genutzt ---
$adminRoutesPath = Join-Path $serverRoot "app\admin\routes.py"
if (Test-Path $adminRoutesPath) {
  $r = Read-Utf8PreserveBom $adminRoutesPath
  $orig = [string]$r.text
  $hasBom = [bool]$r.hasBom

  $lines = [regex]::Split($orig, "\r?\n")
  $out = New-Object System.Collections.Generic.List[string]

  $futureSeen = $false
  for ($i=0; $i -lt $lines.Length; $i++) {
    $ln = $lines[$i]
    if ($ln.Trim() -eq "from __future__ import annotations") {
      if (-not $futureSeen) {
        $out.Add("from __future__ import annotations") | Out-Null
        $futureSeen = $true
      }
      continue
    }
    $out.Add($ln) | Out-Null
  }

  $new = ($out.ToArray() -join "`n")

  # Depends import nur falls benutzt
  if ($new -match '\bDepends\s*\(') {
    if ($new -notmatch '(?m)^\s*from\s+fastapi\s+import\s+.*\bDepends\b') {
      if ($new -match '(?m)^\s*from\s+fastapi\s+import\s+(?<items>.+)\s*$') {
        $new = [regex]::Replace(
          $new,
          '(?m)^\s*from\s+fastapi\s+import\s+(?<items>.+)\s*$',
          { param($m) "from fastapi import " + $m.Groups["items"].Value.TrimEnd() + ", Depends" },
          1
        )
      } else {
        # nach __future__ einfügen
        $new = [regex]::Replace(
          $new,
          '(?m)^(from\s+__future__\s+import\s+annotations\s*)$',
          '$1' + "`nfrom fastapi import Depends",
          1
        )
      }
    }
  }

  if ($new -ne $orig) {
    Write-Utf8PreserveBom $adminRoutesPath $new $hasBom
    Ok "admin/routes.py: __future__ dedupliziert (+Depends falls nötig)"
  } else {
    Ok "admin/routes.py: keine Änderung nötig"
  }
} else {
  Warn "admin/routes.py nicht gefunden: $adminRoutesPath"
}

# --- 3) app/auth/routes.py: Newline am EOF sicherstellen ---
$authRoutesPath = Join-Path $serverRoot "app\auth\routes.py"
if (Test-Path $authRoutesPath) {
  $r = Read-Utf8PreserveBom $authRoutesPath
  $orig = [string]$r.text
  $hasBom = [bool]$r.hasBom

  $new = Ensure-Trailing-Newline $orig

  if ($new -ne $orig) {
    Write-Utf8PreserveBom $authRoutesPath $new $hasBom
    Ok "auth/routes.py: trailing newline ergänzt"
  } else {
    Ok "auth/routes.py: keine Änderung nötig"
  }
} else {
  Warn "auth/routes.py nicht gefunden: $authRoutesPath"
}

# --- 4) scripts/masterclipboard.py: falsche Extension (PowerShell im .py) -> löschen ---
$badScript = Join-Path $serverRoot "scripts\masterclipboard.py"
if (Test-Path $badScript) {
  $txt = (Get-Content -Path $badScript -Raw -Encoding UTF8)
  if ($txt -match 'Set-StrictMode' -or $txt -match '\$ErrorActionPreference') {
    Remove-Item -Force $badScript
    Ok "scripts/masterclipboard.py gelöscht (PowerShell-Inhalt im .py)"
  } else {
    Warn "scripts/masterclipboard.py existiert, aber sieht nicht nach PowerShell aus – nicht gelöscht."
  }
} else {
  Ok "scripts/masterclipboard.py: nicht vorhanden"
}

Ok "FERTIG ✅"
