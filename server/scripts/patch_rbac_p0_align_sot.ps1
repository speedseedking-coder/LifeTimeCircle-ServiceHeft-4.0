# server/scripts/patch_rbac_p0_align_sot.ps1
# P0: RBAC/Exports an docs/03_RIGHTS_MATRIX.md (SoT) angleichen
# - Transfer/Übergabe/Interner Verkauf: NUR vip/dealer (admin/superadmin NICHT)
# - admin-routes: admin ODER superadmin darf Admin-Endpoints nutzen (ohne superadmin-provisioning)
# - require_roles(...admin...): superadmin ergänzen (wo sinnvoll)
# - export.py: KDF für Full-Export Encryption Key via HMAC(sha256) statt sha256(secret+"|...")

$ErrorActionPreference = "Stop"

function Apply-Replacements {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [Parameter(Mandatory=$true)][array]$Rules
  )
  if (-not (Test-Path $FilePath)) {
    throw "Datei nicht gefunden: $FilePath"
  }

  $orig = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8
  $text = $orig
  $changed = $false

  foreach ($r in $Rules) {
    $pattern = $r.Pattern
    $replacement = $r.Replacement
    $isRegex = $r.IsRegex

    if ($isRegex) {
      if ($text -match $pattern) {
        $text = [regex]::Replace($text, $pattern, $replacement)
        $changed = $true
      }
    } else {
      if ($text.Contains($pattern)) {
        $text = $text.Replace($pattern, $replacement)
        $changed = $true
      }
    }
  }

  if ($changed -and ($text -ne $orig)) {
    Set-Content -LiteralPath $FilePath -Value $text -Encoding UTF8 -NoNewline
    return $true
  }
  return $false
}

$changedFiles = New-Object System.Collections.Generic.List[string]

# -----------------------
# 1) server/app/deps.py
# -----------------------
$pathDeps = Join-Path $PSScriptRoot "..\app\deps.py" | Resolve-Path
$rulesDeps = @(
  @{ IsRegex = $true; Pattern = 'VIP/Dealer/Admin/Superadmin'; Replacement = 'VIP/Dealer' },
  # allowed-set für require_vip_or_dealer: NUR vip/dealer
  @{ IsRegex = $true; Pattern = '_enforce\(\s*user\s*,\s*\{\s*"vip"\s*,\s*"dealer"\s*,\s*"admin"\s*,\s*"superadmin"\s*\}\s*\)'; Replacement = '_enforce(user, {"vip", "dealer"})' }
)

if (Apply-Replacements -FilePath $pathDeps -Rules $rulesDeps) { $changedFiles.Add("$pathDeps") | Out-Null }

# ---------------------------
# 2) server/app/auth/deps.py
# ---------------------------
$pathAuthDeps = Join-Path $PSScriptRoot "..\app\auth\deps.py" | Resolve-Path
$rulesAuthDeps = @(
  # "Normale" eingeloggte Nutzer: superadmin ergänzen
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"user"\s*,\s*"vip"\s*,\s*"dealer"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("user", "vip", "dealer", "admin", "superadmin")' },

  # Transfer/Übergabe: NUR vip/dealer (admin/superadmin NICHT)
  @{ IsRegex = $true; Pattern = 'VIP/Dealer/Admin'; Replacement = 'VIP/Dealer' },
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"vip"\s*,\s*"dealer"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("vip", "dealer")' },

  # dealer/admin => dealer/admin/superadmin
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"dealer"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("dealer", "admin", "superadmin")' },

  # moderator/admin => moderator/admin/superadmin
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"moderator"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("moderator", "admin", "superadmin")' },

  # require_admin: admin => admin/superadmin (nur dort, wo es als return-line vorkommt)
  @{ IsRegex = $true; Pattern = 'return\s+require_roles\(\s*"admin"\s*\)\(user=user\)'; Replacement = 'return require_roles("admin", "superadmin")(user=user)  # type: ignore[arg-type]' }
)

if (Apply-Replacements -FilePath $pathAuthDeps -Rules $rulesAuthDeps) { $changedFiles.Add("$pathAuthDeps") | Out-Null }

# ------------------------------
# 3) server/app/admin/routes.py
# ------------------------------
$pathAdminRoutes = Join-Path $PSScriptRoot "..\app\admin\routes.py" | Resolve-Path
$rulesAdminRoutes = @(
  # Admin-Endpunkte: admin ODER superadmin darf nutzen
  @{ IsRegex = $true; Pattern = 'Depends\(\s*require_roles\(\s*"admin"\s*\)\s*\)'; Replacement = 'Depends(require_roles("admin", "superadmin"))' },
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"admin"\s*\)'; Replacement = 'require_roles("admin", "superadmin")' }
)

if (Apply-Replacements -FilePath $pathAdminRoutes -Rules $rulesAdminRoutes) { $changedFiles.Add("$pathAdminRoutes") | Out-Null }

# ------------------------------------
# 4) server/app/routers/masterclipboard.py
# ------------------------------------
$pathMC = Join-Path $PSScriptRoot "..\app\routers\masterclipboard.py" | Resolve-Path
$rulesMC = @(
  # dealer/admin => dealer/admin/superadmin
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"dealer"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("dealer", "admin", "superadmin")' }
)

if (Apply-Replacements -FilePath $pathMC -Rules $rulesMC) { $changedFiles.Add("$pathMC") | Out-Null }

# -----------------------------
# 5) server/app/routers/export.py
# -----------------------------
$pathExport = Join-Path $PSScriptRoot "..\app\routers\export.py" | Resolve-Path

# a) ensure import hmac exists (wenn sha256 importiert wird)
$exportOrig = Get-Content -LiteralPath $pathExport -Raw -Encoding UTF8
if ($exportOrig -notmatch '(?m)^\s*import\s+hmac\s*$') {
  if ($exportOrig -match '(?m)^\s*from\s+hashlib\s+import\s+sha256\s*$') {
    $exportNew = [regex]::Replace($exportOrig, '(?m)^\s*from\s+hashlib\s+import\s+sha256\s*$',
      "import hmac`nfrom hashlib import sha256")
    if ($exportNew -ne $exportOrig) {
      Set-Content -LiteralPath $pathExport -Value $exportNew -Encoding UTF8 -NoNewline
      $changedFiles.Add("$pathExport") | Out-Null
      $exportOrig = $exportNew
    }
  } else {
    # Fallback: hmac ganz oben nach erstem Importblock einfügen
    $exportNew = [regex]::Replace($exportOrig, '(?m)^(from\s+\S+\s+import\s+\S+|import\s+\S+.*)$', '$1' + "`nimport hmac", 1)
    if ($exportNew -ne $exportOrig) {
      Set-Content -LiteralPath $pathExport -Value $exportNew -Encoding UTF8 -NoNewline
      $changedFiles.Add("$pathExport") | Out-Null
      $exportOrig = $exportNew
    }
  }
}

$rulesExport = @(
  # dealer/admin => dealer/admin/superadmin (redacted)
  @{ IsRegex = $true; Pattern = 'require_roles\(\s*"dealer"\s*,\s*"admin"\s*\)'; Replacement = 'require_roles("dealer", "admin", "superadmin")' },

  # KDF: sha256(secret+"|export|full") -> HMAC(secret, "export|full", sha256)
  @{ IsRegex = $true; Pattern = 'digest\s*=\s*sha256\(\(\s*secret_key\s*\+\s*"\|export\|full"\s*\)\.encode\("utf-8"\)\)\.digest\(\)'; Replacement = 'digest = hmac.new(secret_key.encode("utf-8"), b"export|full", sha256).digest()' }
)

if (Apply-Replacements -FilePath $pathExport -Rules $rulesExport) { $changedFiles.Add("$pathExport") | Out-Null }

# -----------------------
# Ergebnis ausgeben
# -----------------------
if ($changedFiles.Count -eq 0) {
  Write-Host "OK: Keine Änderungen nötig (keine passenden Treffer)." -ForegroundColor Green
} else {
  Write-Host "OK: Gepatchte Dateien:" -ForegroundColor Green
  $changedFiles | Sort-Object -Unique | ForEach-Object { Write-Host " - $_" }
}

Write-Host ""
Write-Host "NEXT (prüfen):" -ForegroundColor Cyan
Write-Host '  rg -n "Verkauf/Übergabe|Übergabe-QR|require_vip_or_dealer|VIP/Dealer/Admin|vip\", \"dealer\", \"admin\"|superadmin\" behandelt" app -S'
Write-Host "  poetry run pytest"
