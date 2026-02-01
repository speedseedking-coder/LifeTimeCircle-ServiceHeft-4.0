Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8([string]$Path) { Get-Content -Path $Path -Raw -Encoding UTF8 }

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

$serverRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $serverRoot "app/core/security.py"

if (-not (Test-Path $target)) {
  throw "Nicht gefunden: $target"
}

$text = Read-Utf8 $target

# Patch setzt voraus, dass decode_session_token bereits existiert (Marker war ja da).
if ($text -notmatch "def\s+decode_session_token\s*\(") {
  throw "decode_session_token() fehlt in app/core/security.py. Bitte nicht manuell basteln – erst Script/Stand prüfen."
}

# 1) get_current_actor Block sauber ersetzen (inkl. korrekter Indentation)
$patternA = '(?ms)^[ \t]*def[ \t]+get_current_actor\s*\([\s\S]*?(?=^[ \t]*def[ \t]+require_roles\b)'
$patternB = '(?ms)^[ \t]*def[ \t]+get_current_actor\s*\([\s\S]*\Z'

$replacement = @"
def get_current_actor(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
):
    if not creds:
        _deny(401, "unauthorized")

    token = getattr(creds, "credentials", None)
    if not token:
        _deny(401, "unauthorized")

    try:
        return decode_token(token)
    except HTTPException as e:
        # SESSION_TOKEN_FALLBACK_LTC
        if getattr(e, "status_code", None) != 401:
            raise
        return decode_session_token(token)

"@

if ([regex]::IsMatch($text, $patternA)) {
  $text = [regex]::Replace($text, $patternA, $replacement, [System.Text.RegularExpressions.RegexOptions]::Multiline)
} elseif ([regex]::IsMatch($text, $patternB)) {
  # falls require_roles nicht direkt folgt (edge)
  $text = [regex]::Replace($text, $patternB, $replacement, [System.Text.RegularExpressions.RegexOptions]::Multiline)
} else {
  throw "Konnte get_current_actor(...) Block nicht finden."
}

Write-Utf8NoBom -Path $target -Content $text
Write-Host "OK: get_current_actor() Indentation repariert: $target"
