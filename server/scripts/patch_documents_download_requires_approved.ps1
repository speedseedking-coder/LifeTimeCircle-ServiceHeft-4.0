param(
  [string]$RouterPath = (Join-Path $PSScriptRoot "..\app\routers\documents.py")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $RouterPath)) {
  throw "Router file not found: $RouterPath"
}

$marker = "# Quarantine-by-default: Download für non-admin nur bei Status APPROVED (deny-by-default)"

$src = Get-Content -Raw -Encoding UTF8 $RouterPath

if ($src -like "*$marker*") {
  Write-Host "OK: already patched -> $RouterPath"
  exit 0
}

$decor = '@router.get("/{doc_id}/download")'
$decorIdx = $src.IndexOf($decor)
if ($decorIdx -lt 0) {
  throw "Could not find download route decorator: $decor"
}

$tail = $src.Substring($decorIdx)

# Insert directly before: path = get_document_path_for_download(doc_id)
$pathMatch = [regex]::Match(
  $tail,
  '(?m)^(?<indent>[ \t]*)path\s*=\s*get_document_path_for_download\s*\(\s*doc_id\s*\)\s*$'
)
if (-not $pathMatch.Success) {
  throw "Could not find line: path = get_document_path_for_download(doc_id) inside download handler."
}

$indent = $pathMatch.Groups['indent'].Value
$prefix = $tail.Substring(0, $pathMatch.Index)

# Detect actor/current-user variable (role or user_id usage)
$roleVar = $null

$rm = [regex]::Match($prefix, "(?m)(?<v>[A-Za-z_]\w*)\s*\[\s*['""]role['""]\s*\]")
if ($rm.Success) { $roleVar = $rm.Groups['v'].Value }

if (-not $roleVar) {
  $rm = [regex]::Match($prefix, "(?m)(?<v>[A-Za-z_]\w*)\.get\(\s*['""]role['""]\s*\)")
  if ($rm.Success) { $roleVar = $rm.Groups['v'].Value }
}

if (-not $roleVar) {
  $rm = [regex]::Match($prefix, "(?m)(?<v>[A-Za-z_]\w*)\s*\[\s*['""]user_id['""]\s*\]")
  if ($rm.Success) { $roleVar = $rm.Groups['v'].Value }
}

if (-not $roleVar) {
  throw "Could not detect current-user variable in download handler. Ensure handler uses something like X['role'] or X['user_id']."
}

# Detect document/meta variable (used for filename/media_type OR owner_user_id)
$metaVar = $null

$mm = [regex]::Match($prefix, "(?m)(?<v>[A-Za-z_]\w*)\s*\[\s*['""]owner_user_id['""]\s*\]")
if ($mm.Success) { $metaVar = $mm.Groups['v'].Value }

if (-not $metaVar) {
  $mm = [regex]::Match($prefix, "(?m)(?<v>[A-Za-z_]\w*)\.get\(\s*['""]owner_user_id['""]\s*\)")
  if ($mm.Success) { $metaVar = $mm.Groups['v'].Value }
}

if (-not $metaVar) {
  $mm = [regex]::Match($prefix, "(?m)(?:filename|media_type)\s*=\s*(?<v>[A-Za-z_]\w*)\s*(?:\.|\[)")
  if ($mm.Success) { $metaVar = $mm.Groups['v'].Value }
}

if (-not $metaVar) {
  # last resort: assignment pattern: X = something(doc_id)
  $mm = [regex]::Match($prefix, "(?m)^\s*(?<v>[A-Za-z_]\w*)\s*=\s*[A-Za-z_]\w*\(\s*doc_id\s*\)\s*$")
  if ($mm.Success) { $metaVar = $mm.Groups['v'].Value }
}

if (-not $metaVar) {
  throw "Could not detect meta/document variable in download handler. Ensure handler has meta/doc dict in scope."
}

$i0 = $indent
$i1 = $indent + "    "
$i2 = $indent + "        "

$injectLines = @()
$injectLines += $i0 + $marker
$injectLines += $i0 + "__doc = $metaVar"
$injectLines += $i0 + "if isinstance(__doc, dict) and isinstance(__doc.get('doc'), dict):"
$injectLines += $i1 + "__doc = __doc['doc']"
$injectLines += $i0 + "__st = str((__doc.get('status') or '')).strip().lower() if isinstance(__doc, dict) else ''"
$injectLines += $i0 + "__role = ''"
$injectLines += $i0 + "try:"
$injectLines += $i1 + "if isinstance($roleVar, dict):"
$injectLines += $i2 + "__role = str(($roleVar.get('role') or '')).strip().lower()"
$injectLines += $i1 + "else:"
$injectLines += $i2 + "__role = str(getattr($roleVar, 'role', '')).strip().lower()"
$injectLines += $i0 + "except Exception:"
$injectLines += $i1 + "__role = ''"
$injectLines += $i0 + "if __role not in ('admin', 'superadmin') and __st != 'approved':"
$injectLines += $i1 + "raise HTTPException(status_code=404, detail='not_found')"
$injectLines += ""

$inject = ($injectLines -join "`n")

$insertPos = $decorIdx + $pathMatch.Index
$new = $src.Insert($insertPos, $inject)

Set-Content -Path $RouterPath -Encoding UTF8 -Value $new

Write-Host "OK: patched $RouterPath"
Write-Host " - non-admin download now requires status=approved (404 otherwise)."