# server/scripts/patch_sale_transfer_status_participant_only.ps1
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

# --- locate router file (support minor naming variants) ---
$candidates = @(
  (Join-Path $RepoRoot "server/app/routers/sale_transfer.py"),
  (Join-Path $RepoRoot "server/app/routers/sale_transfer.py")
) | Select-Object -Unique

$routerPath = $null
foreach ($p in $candidates) {
  if (Test-Path $p) { $routerPath = $p; break }
}
if (-not $routerPath) {
  Die "FEHLT: Router nicht gefunden. Erwartet: server/app/routers/sale_transfer.py"
}

$content = Get-Content -LiteralPath $routerPath -Raw -Encoding UTF8

# idempotent marker
if ($content -match "ONLY_INITIATOR_OR_REDEEMER") {
  Info "OK: $routerPath ist bereits gepatcht (Marker gefunden)."
  exit 0
}

# detect newline style
$nl = "`n"
if ($content.Contains("`r`n")) { $nl = "`r`n" }

# --- ensure HTTPException import exists (best-effort) ---
if ($content -notmatch "\bHTTPException\b") {
  $patched = $false

  # try: from fastapi import ...
  $content2 = [regex]::Replace(
    $content,
    '^(from\s+fastapi\s+import\s+)([^\r\n]+)$',
    {
      param($m)
      $prefix = $m.Groups[1].Value
      $imports = $m.Groups[2].Value
      if ($imports -match '\bHTTPException\b') { return $m.Value }
      $script:patched = $true
      return ($prefix + $imports.TrimEnd() + ", HTTPException")
    },
    [System.Text.RegularExpressions.RegexOptions]::Multiline,
    1
  )

  if ($patched) {
    $content = $content2
    Info "OK: HTTPException Import ergänzt."
  } else {
    Info "WARN: HTTPException Import nicht automatisch ergänzt. Falls später NameError: HTTPException → bitte manuell importieren."
  }
}

# --- find status endpoint block (decorator contains 'status' OR function name contains 'status') ---
# pattern A: decorator + def
$rxDecor = '(?ms)^[ \t]*@(?<router>\w+)\.get\(\s*(?<args>[^)]*["''](?<path>[^"'']*status[^"'']*)["''][^)]*)\)\s*\r?\n(?<indent>[ \t]*)def\s+(?<fn>\w+)\s*\('
$m = [regex]::Match($content, $rxDecor)
$fnName = $null
$defIndent = ""
$defIndex = -1

if ($m.Success) {
  $fnName = $m.Groups["fn"].Value
  $defIndent = $m.Groups["indent"].Value
  $defIndex = $m.Groups[0].Index + $m.Groups[0].Value.LastIndexOf("def")
} else {
  # pattern B: function named *status*
  $rxFn = '(?m)^(?<indent>[ \t]*)def\s+(?<fn>\w*status\w*)\s*\('
  $m2 = [regex]::Match($content, $rxFn)
  if ($m2.Success) {
    $fnName = $m2.Groups["fn"].Value
    $defIndent = $m2.Groups["indent"].Value
    $defIndex = $m2.Index
  } else {
    Die "PATCH-ABBRUCH: Konnte Status-Endpoint nicht finden. Erwartet: @router.get(...status...) oder def *status*."
  }
}

# find function header end: from defIndex to first occurrence of '):' or ')->' with closing '):'
$afterDef = $content.Substring($defIndex)
$headerEnd = [regex]::Match($afterDef, '(?ms)\)\s*(?:->\s*[^:]+)?\s*:\s*').Index
if ($headerEnd -lt 0) {
  Die "PATCH-ABBRUCH: Konnte Funktions-Header nicht parsen (fehlendes ':')."
}
$headerText = $afterDef.Substring(0, $headerEnd + 1)

# actor param name from Depends(require_actor)
$actorName = "actor"
$rxActor = '(?s)(?<name>\w+)\s*=\s*Depends\(\s*require_actor\b'
$ma = [regex]::Match($headerText, $rxActor)
if ($ma.Success) { $actorName = $ma.Groups["name"].Value }

# determine function block end: next decorator/def at same indent
$rxNext = "(?m)^(?:$([regex]::Escape($defIndent)))\s*(?:@|def)\s+"
$mn = [regex]::Match($afterDef, $rxNext, [System.Text.RegularExpressions.RegexOptions]::Multiline, $headerEnd + 1)

$blockEnd = $content.Length
if ($mn.Success) {
  $blockEnd = $defIndex + $mn.Index
}

$fnBlock = $content.Substring($defIndex, $blockEnd - $defIndex)

# extract route param candidates from decorator path if available
$paramCandidates = New-Object System.Collections.Generic.List[string]
if ($m.Success) {
  $path = $m.Groups["path"].Value
  $rxParams = '\{([A-Za-z_][A-Za-z0-9_]*)\}'
  foreach ($pm in [regex]::Matches($path, $rxParams)) {
    $paramCandidates.Add($pm.Groups[1].Value)
  }
}

# always add common names
foreach ($x in @("tid", "transfer_id", "id")) {
  if (-not $paramCandidates.Contains($x)) { $paramCandidates.Add($x) }
}

# find first fetch assignment line inside fnBlock that references one of the param candidates
$fetchMatch = $null
foreach ($cand in $paramCandidates) {
  $rxFetch = "(?m)^(?<indent>[ \t]+)(?<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*.*\(\s*.*\b$([regex]::Escape($cand))\b.*\)\s*$"
  $mm = [regex]::Match($fnBlock, $rxFetch)
  if ($mm.Success) { $fetchMatch = $mm; break }
}

if (-not $fetchMatch) {
  Die "PATCH-ABBRUCH: Konnte keine Transfer-Fetch-Zeile im Status-Endpoint finden (suche nach '<var> = ...(...tid/transfer_id...)')."
}

$indent2 = $fetchMatch.Groups["indent"].Value
$transferVar = $fetchMatch.Groups["var"].Value

# insert guard after fetch line
$insert = @(
  "${indent2}# ONLY_INITIATOR_OR_REDEEMER: object-level RBAC (Status nur für Initiator oder Redeemer; verhindert ID-Leak)"
  "${indent2}def _get_id(obj, key):"
  "${indent2}    if obj is None:"
  "${indent2}        return None"
  "${indent2}    if isinstance(obj, dict):"
  "${indent2}        return obj.get(key)"
  "${indent2}    return getattr(obj, key, None)"
  "${indent2}_initiator_id = _get_id($transferVar, `"initiator_user_id`")"
  "${indent2}_redeemer_id  = _get_id($transferVar, `"redeemed_by_user_id`")"
  "${indent2}_actor_obj = $actorName"
  "${indent2}if isinstance(_actor_obj, dict):"
  "${indent2}    _actor_id = _actor_obj.get(`"user_id`") or _actor_obj.get(`"id`")"
  "${indent2}else:"
  "${indent2}    _actor_id = getattr(_actor_obj, `"user_id`", None) or getattr(_actor_obj, `"id`", None)"
  "${indent2}if _actor_id not in {_initiator_id, _redeemer_id}:"
  "${indent2}    raise HTTPException(status_code=403, detail=`"forbidden`")"
) -join $nl

$localInsertPos = $fetchMatch.Index + $fetchMatch.Length
$fnBlock2 = $fnBlock.Insert($localInsertPos, $nl + $insert + $nl)

# replace block in full content
$content2 = $content.Substring(0, $defIndex) + $fnBlock2 + $content.Substring($blockEnd)

Set-Content -LiteralPath $routerPath -Value $content2 -Encoding UTF8 -NoNewline
Info "OK: Gepatcht: $routerPath"
Info "NEXT: git diff prüfen, committen, pytest laufen lassen."