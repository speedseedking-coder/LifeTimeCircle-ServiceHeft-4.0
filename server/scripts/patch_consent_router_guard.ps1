param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# repo root (script liegt in server/scripts)
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "server\app\routers\consent.py"

if (-not (Test-Path $target)) {
  throw "Target not found: $target"
}

# 1) Modul finden, wo forbid_moderator definiert ist
$def = Get-ChildItem -Path (Join-Path $repoRoot "server\app") -Recurse -Filter "*.py" |
  Select-String -Pattern "^\s*def\s+forbid_moderator\b" -List |
  Select-Object -First 1

if (-not $def) {
  throw "Konnte 'def forbid_moderator' unter server/app nicht finden."
}

# Pfad: ...\server\app\auth\deps.py -> Modul: app.auth.deps
$serverDir = Join-Path $repoRoot "server"
$rel = $def.Path.Substring($serverDir.Length).TrimStart('\','/')
$mod = $rel.Replace('\','/').Replace('/','.')
if ($mod.EndsWith(".py")) { $mod = $mod.Substring(0, $mod.Length - 3) }

# 2) consent.py laden
$text = Get-Content -Raw -Encoding UTF8 $target

# 3) fastapi Depends import sicherstellen
if ($text -match "(?m)^\s*from\s+fastapi\s+import\s+") {
  if ($text -notmatch "(?m)^\s*from\s+fastapi\s+import\s+.*\bDepends\b") {
    $text = [regex]::Replace(
      $text,
      "(?m)^(?<p>\s*from\s+fastapi\s+import\s+)(?<rest>.+)$",
      '${p}Depends, ${rest}',
      1
    )
  }
} else {
  throw "Kein 'from fastapi import ...' gefunden in consent.py"
}

# 4) forbid_moderator import sicherstellen
if ($text -notmatch "(?m)^\s*from\s+$([regex]::Escape($mod))\s+import\s+.*\bforbid_moderator\b") {
  # nach fastapi-import block einfügen
  $text = [regex]::Replace(
    $text,
    "(?m)^(from\s+fastapi\s+import\s+.+\r?\n)",
    "`$1from $mod import forbid_moderator`r`n",
    1
  )
}

# 5) Router-Definition patchen (idempotent)
if ($text -notmatch 'APIRouter\([^)]*dependencies\s*=\s*\[\s*Depends\(\s*forbid_moderator\s*\)\s*\]') {
  $text = [regex]::Replace(
    $text,
    '(?m)^\s*router\s*=\s*APIRouter\(\s*prefix\s*=\s*"/consent"\s*,\s*tags\s*=\s*\[\s*"consent"\s*\]\s*\)\s*$',
    'router = APIRouter(prefix="/consent", tags=["consent"], dependencies=[Depends(forbid_moderator)])'
  )
}

# 6) EOF newline sicherstellen
if (-not $text.EndsWith("`n")) { $text += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $text
Write-Host "OK: patched $target (Depends + forbid_moderator + router dependencies)"