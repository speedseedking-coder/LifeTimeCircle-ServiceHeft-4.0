Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8([string]$Path) { Get-Content -Path $Path -Raw -Encoding UTF8 }

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

$serverRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $serverRoot "app\routers\masterclipboard.py"

if (-not (Test-Path $target)) {
  throw "Zieldatei nicht gefunden: $target"
}

$text = Read-Utf8 $target

# Idempotent: Wenn bereits gepatcht, nichts tun
if ($text -match "def require_masterclipboard_roles" -and $text -match "get_auth_context") {
  Write-Host "SKIP: masterclipboard.py ist bereits auf Session-Auth gepatcht: $target"
  exit 0
}

# 1) Import: core.security -> Actor behalten, require_roles entfernen
$text = [regex]::Replace(
  $text,
  '(?m)^\s*from\s+app\.core\.security\s+import\s+(?<items>.+)\s*$',
  {
    param($m)
    $items = $m.Groups["items"].Value
    if ($items -match '\bActor\b' -and $items -match '\brequire_roles\b') {
      return "from app.core.security import Actor"
    }
    return $m.Value
  }
)

# 2) Auth-RBAC Import ergänzen, falls fehlt
if ($text -notmatch '(?m)^\s*from\s+app\.auth\.rbac\s+import\s+AuthContext,\s*get_auth_context\s*$') {
  if ($text -match '(?m)^\s*from\s+app\.core\.security\s+import\s+Actor\s*$') {
    $text = [regex]::Replace(
      $text,
      '(?m)^\s*from\s+app\.core\.security\s+import\s+Actor\s*$',
      "from app.core.security import Actor`nfrom app.auth.rbac import AuthContext, get_auth_context",
      1
    )
  } else {
    $text = "from app.auth.rbac import AuthContext, get_auth_context`n" + $text
  }
}

# 3) FastAPI Imports sicherstellen: Depends + HTTPException
$fastapiImport = [regex]::Match($text, '(?m)^\s*from\s+fastapi\s+import\s+(?<items>.+)\s*$')
if ($fastapiImport.Success) {
  $items = $fastapiImport.Groups["items"].Value
  $need = @()
  if ($items -notmatch '\bDepends\b') { $need += "Depends" }
  if ($items -notmatch '\bHTTPException\b') { $need += "HTTPException" }
  if ($need.Count -gt 0) {
    $newItems = ($items.Trim() + ", " + ($need -join ", ")) -replace '\s+', ' '
    $text = $text.Replace($fastapiImport.Value, "from fastapi import $newItems")
  }
} else {
  $text = "from fastapi import Depends, HTTPException`n" + $text
}

# 4) Helper Dependency einfügen (Session-Auth -> Actor)
$routerDef = [regex]::Match($text, '(?m)^\s*router\s*=\s*APIRouter\b')
if (-not $routerDef.Success) {
  throw "Konnte 'router = APIRouter' in masterclipboard.py nicht finden."
}

$helper = @"
# --- Session-Auth Adapter für Masterclipboard (kein JWT) ---
# Masterclipboard hängt an serverseitigen Sessions (AuthContext) und mappt auf Actor.
# Rollenprüfung bleibt deny-by-default; wenn nicht erlaubt -> 403 (nicht 401).
def require_masterclipboard_roles(*allowed: str):
    allowed_set = set(allowed)

    def _dep(ctx: AuthContext = Depends(get_auth_context)) -> Actor:
        if ctx.role not in allowed_set:
            raise HTTPException(status_code=403, detail="forbidden")
        # org_id: MVP-safe Default = user_id (serverseitig abgeleitet, nicht user-supplied)
        return Actor(subject_id=str(ctx.user_id), role=str(ctx.role), org_id=str(ctx.user_id))

    return _dep

"@

$text = $text.Insert($routerDef.Index, $helper)

# 5) Alle Depends(require_roles(...)) -> Depends(require_masterclipboard_roles(...))
$text = [regex]::Replace(
  $text,
  'Depends\(\s*require_roles\s*\(',
  'Depends(require_masterclipboard_roles('
)

# 6) Restliche require_roles Imports entfernen (falls noch vorhanden)
$text = [regex]::Replace(
  $text,
  '(?m)^\s*from\s+app\.core\.security\s+import\s+Actor\s*,\s*require_roles\s*$',
  'from app.core.security import Actor'
)

Write-Utf8NoBom -Path $target -Content $text
Write-Host "OK: Masterclipboard auf Session-Auth gepatcht: $target"
Write-Host "NEXT: Uvicorn neu starten und /api/masterclipboard/sessions erneut testen."
