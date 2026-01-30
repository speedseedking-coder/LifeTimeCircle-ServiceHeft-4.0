# Patch: entfernt datetime.utcnow Deprecation in SQLAlchemy Defaults/OnUpdate
# - default=datetime.utcnow / onupdate=datetime.utcnow -> lambda: datetime.now(timezone.utc)
# - default=datetime.datetime.utcnow / onupdate=datetime.datetime.utcnow -> lambda: datetime.datetime.now(datetime.timezone.utc)
# - datetime.utcnow() / datetime.datetime.utcnow() -> timezone-aware now(...)
#
# Ausführen im server-Ordner:
#   pwsh -ExecutionPolicy Bypass -File .\scripts\patch_sqlalchemy_utcnow.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$appRoot = Join-Path $serverRoot "app"

if (-not (Test-Path $appRoot)) {
  Write-Host "FEHLT: app Ordner nicht gefunden: $appRoot"
  exit 1
}

function Backup-File([string]$path) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  Copy-Item $path "$path.bak.$ts" -Force
}

$files = Get-ChildItem $appRoot -Recurse -File -Filter "*.py"
$changed = @()

foreach ($f in $files) {
  $raw = Get-Content -Path $f.FullName -Raw -Encoding UTF8
  $orig = $raw

  # 1) Calls (mit Klammern)
  $raw = $raw -replace 'datetime\.datetime\.utcnow\(\)', 'datetime.datetime.now(datetime.timezone.utc)'
  $raw = $raw -replace 'datetime\.utcnow\(\)', 'datetime.now(timezone.utc)'

  # 2) SQLAlchemy Column Defaults/OnUpdate (ohne Klammern)
  $raw = $raw -replace '(\bdefault\s*=\s*)datetime\.datetime\.utcnow\b', '$1(lambda: datetime.datetime.now(datetime.timezone.utc))'
  $raw = $raw -replace '(\bonupdate\s*=\s*)datetime\.datetime\.utcnow\b', '$1(lambda: datetime.datetime.now(datetime.timezone.utc))'

  $raw = $raw -replace '(\bdefault\s*=\s*)datetime\.utcnow\b', '$1(lambda: datetime.now(timezone.utc))'
  $raw = $raw -replace '(\bonupdate\s*=\s*)datetime\.utcnow\b', '$1(lambda: datetime.now(timezone.utc))'

  if ($raw -ne $orig) {
    # Import-Fix nur wenn wir timezone.utc verwenden und file "from datetime import ..." nutzt
    if ($raw -match 'timezone\.utc') {
      if ($raw -match '(?m)^\s*from\s+datetime\s+import\s+([^\r\n]+)\s*$') {
        $raw = [regex]::Replace(
          $raw,
          '(?m)^\s*from\s+datetime\s+import\s+([^\r\n]+)\s*$',
          {
            param($m)
            $imports = $m.Groups[1].Value.Trim()
            if ($imports -match '\btimezone\b') { return $m.Value }
            return "from datetime import $imports, timezone"
          },
          1
        )
      }
    }

    Backup-File $f.FullName
    Set-Content -Path $f.FullName -Value $raw -Encoding UTF8
    $changed += $f.FullName
  }
}

if ($changed.Count -eq 0) {
  Write-Host "OK: Keine utcnow-Stellen mehr im app/ gefunden."
} else {
  Write-Host "OK: Gepatchte Dateien:"
  $changed | ForEach-Object { Write-Host (" - " + $_) }
}

Write-Host "FERTIG ✅"
