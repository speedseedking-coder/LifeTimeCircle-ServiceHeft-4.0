param(
  [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Die([string]$msg) {
  Write-Error $msg
  exit 1
}

function Info([string]$msg) {
  Write-Host $msg
}

$routerPath = Join-Path $RepoRoot "server/app/routers/sale_transfer.py"
if (-not (Test-Path $routerPath)) {
  Die "FEHLT: $routerPath (Script aus Repo-Root starten)."
}

$content = Get-Content -LiteralPath $routerPath -Raw -Encoding UTF8

# idempotent marker
if ($content -match "ONLY_INITIATOR_OR_REDEEMER") {
  Info "OK: sale_transfer.py ist bereits gepatcht (Marker gefunden)."
  exit 0
}

$nl = "`n"
if ($content.Contains("`r`n")) { $nl = "`r`n" }

# Ensure HTTPException import exists (best-effort patch)
if ($content -notmatch "\bHTTPException\b") {
  $patched = $false

  # common: "from fastapi import APIRouter, Depends, HTTPException"
  $content2 = [regex]::Replace(
    $content,
    '^(from\s+fastapi\s+import\s+)([^\r\n]+)$',
    {
      param($m)
      $prefix = $m.Groups[1].Value
      $imports = $m.Groups[2].Value
      if ($imports -match '\bHTTPException\b') { return $m.Value }
      $patched = $true
      return ($prefix + $imports.TrimEnd() + ", HTTPException")
    },
    [System.Text.RegularExpressions.RegexOptions]::Multiline,
    1
  )

  if (-not $patched) {
    # alternate: already split imports, do nothing but warn
    Info "WARN: Konnte HTTPException Import nicht automatisch ergänzen (prüfe Imports in sale_transfer.py)."
  } else {
    $content = $content2
    Info "OK: HTTPException Import ergänzt."
  }
}

# locate status route area
$idx = $content.IndexOf("/sale/transfer/status")
if ($idx -lt 0) { $idx = $content.IndexOf("sale/transfer/status") }
if ($idx -lt 0) {
  Die "NICHT GEFUNDEN: Route-String 'sale/transfer/status' in $routerPath"
}

$after = $content.Substring($idx)

# find first assignment near the route that fetches a transfer-like object (contains tid or transfer_id in call args)
$rx1 = '(?m)^(?<indent>[ \t]*)(?<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*.*\(\s*.*\b(tid|transfer_id)\b.*\)\s*$'
$m = [regex]::Match($after, $rx1)
if (-not $m.Success) {
  Die "PATCH-ABBRUCH: Konnte keine passende Transfer-Fetch-Zeile nahe der Status-Route finden (suche nach '<var> = ...(...tid|transfer_id...)')."
}

$indent = $m.Groups["indent"].Value
$var    = $m.Groups["var"].Value

$insert = @(
  "${indent}# ONLY_INITIATOR_OR_REDEEMER: object-level RBAC (Status nur für Initiator oder Redeemer; verhindert ID-Leak)"
  "${indent}def _field(obj, key):"
  "${indent}    if isinstance(obj, dict):"
  "${indent}        return obj.get(key)"
  "${indent}    return getattr(obj, key, None)"
  "${indent}_initiator_id = _field($var, `"initiator_user_id`")"
  "${indent}_redeemer_id  = _field($var, `"redeemed_by_user_id`")"
  "${indent}_actor_id = (actor.get(`"user_id`") if isinstance(actor, dict) else (getattr(actor, `"user_id`", None) or getattr(actor, `"id`", None)))"
  "${indent}if _actor_id not in {_initiator_id, _redeemer_id}:"
  "${indent}    raise HTTPException(status_code=403, detail=`"forbidden`")"
) -join $nl

# insert directly after the matched fetch line
$insertPos = $idx + $m.Index + $m.Length
$content = $content.Insert($insertPos, $nl + $insert + $nl)

Set-Content -LiteralPath $routerPath -Value $content -Encoding UTF8 -NoNewline
Info "OK: Gepatcht: $routerPath"
Info "NEXT: pytest laufen lassen + Integrationstest ergänzen (VIP/Dealer fremder Actor -> 403)."