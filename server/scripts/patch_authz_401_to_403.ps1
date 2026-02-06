# server\scripts\patch_rbac_401_to_403.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Patch-Function401To403([string]$Text, [string]$FuncName) {
  $lines = $Text -split "`r?`n"
  $changed = $false
  $inFunc = $false
  $funcIndent = 0

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    # Funktionsstart
    if (-not $inFunc -and $line -match ("^(?<ind>\s*)def\s+" + [regex]::Escape($FuncName) + "\s*\(")) {
      $inFunc = $true
      $funcIndent = $matches["ind"].Length
      continue
    }

    if ($inFunc) {
      # Funktionsende: nächste def/class auf gleicher/kleinerer Indentation
      if ($line -match "^(?<ind>\s*)(def|class)\s+" -and $matches["ind"].Length -le $funcIndent) {
        $inFunc = $false
        # bewusst: die Zeile nicht anfassen (neue def/class)
      } else {
        $new = $line

        # Statuscode 401 -> 403 (nur innerhalb der Funktion!)
        $new = $new -replace "status_code\s*=\s*status\.HTTP_401_UNAUTHORIZED\b", "status_code=status.HTTP_403_FORBIDDEN"
        $new = $new -replace "status_code\s*=\s*401\b", "status_code=403"

        # detail unauthorized -> forbidden (nur innerhalb der Funktion!)
        $new = $new -replace 'detail\s*=\s*"unauthorized"', 'detail="forbidden"'
        $new = $new -replace "detail\s*=\s*'unauthorized'", "detail='forbidden'"

        if ($new -ne $line) {
          $lines[$i] = $new
          $changed = $true
        }
      }
    }
  }

  return @{
    Text    = ($lines -join "`n")
    Changed = $changed
  }
}

function Patch-FileFunction([string]$Path, [string]$FuncName) {
  if (-not (Test-Path $Path)) { return $false }
  $before = [System.IO.File]::ReadAllText($Path)
  $res = Patch-Function401To403 -Text $before -FuncName $FuncName
  if ($res.Changed -and $res.Text -ne $before) {
    Write-Utf8NoBom -Path $Path -Content $res.Text
    return $true
  }
  return $false
}

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$appRoot = Join-Path $serverRoot "app"

$patched = New-Object System.Collections.Generic.List[string]

# 1) export_* Router: _require_roles => bei Rollen-Mismatch 403
$exportFiles = @(
  (Join-Path $appRoot "routers\export_vehicle.py"),
  (Join-Path $appRoot "routers\export_servicebook.py"),
  (Join-Path $appRoot "routers\export_masterclipboard.py")
)

foreach ($f in $exportFiles) {
  if (Test-Path $f) {
    if (Patch-FileFunction -Path $f -FuncName "_require_roles") {
      $patched.Add($f) | Out-Null
      Write-Host "OK gepatcht _require_roles: $f"
    } else {
      Write-Host "OK unverändert _require_roles: $f"
    }
  }
}

# 2) require_roles (zentral) finden + patchen => bei Rollen-Mismatch 403
$pyFiles = Get-ChildItem -Path $appRoot -Recurse -File -Filter "*.py"
$found = $false

foreach ($pf in $pyFiles) {
  $txt = [System.IO.File]::ReadAllText($pf.FullName)
  if ($txt -match "(?m)^\s*def\s+require_roles\s*\(") {
    $found = $true
    if (Patch-FileFunction -Path $pf.FullName -FuncName "require_roles") {
      $patched.Add($pf.FullName) | Out-Null
      Write-Host "OK gepatcht require_roles: $($pf.FullName)"
    } else {
      Write-Host "OK unverändert require_roles: $($pf.FullName)"
    }
  }
}

if (-not $found) {
  throw "def require_roles(...) nicht gefunden. Bitte 'Select-String -Path .\app\**\*.py -Pattern \"def require_roles\" -List' ausführen."
}

Write-Host ""
if ($patched.Count -gt 0) {
  Write-Host "FERTIG ✅ Gepatchte Dateien:"
  $patched | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Host "HINWEIS: Nichts geändert (evtl. war schon überall 403 oder die Stellen sind anders)."
}
