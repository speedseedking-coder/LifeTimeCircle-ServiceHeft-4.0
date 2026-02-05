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

function ReadUtf8([string]$path) {
  return [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
}

function WriteUtf8([string]$path, [string]$text) {
  [System.IO.File]::WriteAllText($path, $text, [System.Text.Encoding]::UTF8)
}

function DetectNewline([string]$text) {
  if ($text.Contains("`r`n")) { return "`r`n" }
  return "`n"
}

function SplitLines([string]$text) {
  return ($text -split "\r?\n", -1)
}

function JoinLines([string[]]$lines, [string]$nl) {
  return [string]::Join($nl, $lines)
}

function EnsureHttpExceptionImport([string[]]$lines) {
  $has = $false
  foreach ($ln in $lines) {
    if ($ln -match "\bHTTPException\b") { $has = $true; break }
  }
  if ($has) { return ,$lines }

  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*from\s+fastapi\s+import\s+') {
      if ($lines[$i] -notmatch "\bHTTPException\b") {
        $lines[$i] = $lines[$i].TrimEnd() + ", HTTPException"
        Info "OK: HTTPException Import ergänzt."
      }
      return ,$lines
    }
  }

  # fallback: add new import near top (after first import block)
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*(import|from)\s+') {
      $insertAt = $i + 1
      $new = New-Object System.Collections.Generic.List[string]
      for ($j=0; $j -lt $lines.Count; $j++) {
        if ($j -eq $insertAt) { $new.Add("from fastapi import HTTPException") }
        $new.Add($lines[$j])
      }
      Info "OK: HTTPException Import als separate Zeile ergänzt."
      return ,$new.ToArray()
    }
  }

  # worst-case: prepend
  $new2 = @("from fastapi import HTTPException") + $lines
  Info "OK: HTTPException Import am Dateianfang ergänzt."
  return ,$new2
}

function FindNextDefIndex([string[]]$lines, [int]$start) {
  for ($i=$start; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*def\s+\w+\s*\(') { return $i }
  }
  return -1
}

function FindFunctionEnd([string[]]$lines, [int]$defIndex) {
  $defLine = $lines[$defIndex]
  $m = [regex]::Match($defLine, '^(\s*)def\s+')
  $baseIndent = ""
  if ($m.Success) { $baseIndent = $m.Groups[1].Value }

  for ($i=$defIndex+1; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($ln -match '^\s*$') { continue }

    # next top-level def/decorator at same indent => function ends
    if ($ln.StartsWith($baseIndent) -and $ln -match '^\s*(def|@)\s+') {
      return $i
    }
  }
  return $lines.Count
}

function ExtractActorParamName([string[]]$lines, [int]$defIndex) {
  # read signature until we hit line ending with ":" after a ")"
  $sig = New-Object System.Collections.Generic.List[string]
  for ($i=$defIndex; $i -lt $lines.Count; $i++) {
    $sig.Add($lines[$i])
    if ($lines[$i] -match '\)\s*(?:->\s*[^:]+)?\s*:\s*$') { break }
  }
  $sigText = [string]::Join(" ", $sig)

  $m = [regex]::Match($sigText, '(?<name>\w+)\s*=\s*Depends\(\s*require_actor\b')
  if ($m.Success) { return $m.Groups["name"].Value }
  return "actor"
}

function ExtractPathParamFromDecorator([string]$decorLine) {
  # example: @router.get("/status/{tid}")
  $m = [regex]::Match($decorLine, '["''](?<path>[^"'']+)["'']')
  if (-not $m.Success) { return "tid" }
  $path = $m.Groups["path"].Value
  $m2 = [regex]::Match($path, '\{(?<p>[A-Za-z_][A-Za-z0-9_]*)\}')
  if ($m2.Success) { return $m2.Groups["p"].Value }
  return "tid"
}

function PatchRouter([string]$routerPath) {
  $text = ReadUtf8 $routerPath
  if ($text -match "ONLY_INITIATOR_OR_REDEEMER") {
    Info "OK: Router bereits gepatcht (Marker gefunden)."
    return $false
  }

  $nl = DetectNewline $text
  $lines = SplitLines $text

  $lines = EnsureHttpExceptionImport $lines

  # find decorator line for status endpoint
  $decorIdx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($ln -match '^\s*@\w+\.get\(' -and $ln -match 'status') {
      $decorIdx = $i
      break
    }
  }
  if ($decorIdx -lt 0) {
    Die "PATCH-ABBRUCH: Status-Decorator nicht gefunden in $routerPath (erwartet: @router.get(...status...))."
  }

  $paramName = ExtractPathParamFromDecorator $lines[$decorIdx]
  $defIdx = FindNextDefIndex $lines ($decorIdx + 1)
  if ($defIdx -lt 0) {
    Die "PATCH-ABBRUCH: def nach Status-Decorator nicht gefunden in $routerPath."
  }

  $endIdx = FindFunctionEnd $lines $defIdx
  $actorName = ExtractActorParamName $lines $defIdx

  # find first assignment inside function body that references paramName
  $assignIdx = -1
  $transferVar = $null
  for ($i=$defIdx+1; $i -lt $endIdx; $i++) {
    $ln = $lines[$i]
    if ($ln -match '^\s+\w+\s*=\s*' -and $ln -match "\b$([regex]::Escape($paramName))\b" -and $ln.Contains("(")) {
      $assignIdx = $i
      $m = [regex]::Match($ln, '^\s*(?<var>[A-Za-z_][A-Za-z0-9_]*)\s*=')
      if ($m.Success) { $transferVar = $m.Groups["var"].Value }
      break
    }
  }
  if ($assignIdx -lt 0 -or -not $transferVar) {
    Die "PATCH-ABBRUCH: Konnte keine passende Fetch-Assignment-Zeile mit '$paramName' im Status-Endpoint finden."
  }

  $indentMatch = [regex]::Match($lines[$assignIdx], '^(\s+)')
  $indent = "    "
  if ($indentMatch.Success) { $indent = $indentMatch.Groups[1].Value }
  $indent2 = $indent + "    "

  $guard = @(
    "${indent}# ONLY_INITIATOR_OR_REDEEMER: object-level RBAC (Status nur für Initiator oder Redeemer; verhindert tid-Enumeration/ID-Leaks)"
    "${indent}def _get_id(obj, key):"
    "${indent2}if obj is None:"
    "${indent2}    return None"
    "${indent2}if isinstance(obj, dict):"
    "${indent2}    return obj.get(key)"
    "${indent2}return getattr(obj, key, None)"
    "${indent}_initiator_id = _get_id($transferVar, `"initiator_user_id`")"
    "${indent}_redeemer_id  = _get_id($transferVar, `"redeemed_by_user_id`")"
    "${indent}_actor_obj = $actorName"
    "${indent}if isinstance(_actor_obj, dict):"
    "${indent2}_actor_id = _actor_obj.get(`"user_id`") or _actor_obj.get(`"id`")"
    "${indent}else:"
    "${indent2}_actor_id = getattr(_actor_obj, `"user_id`", None) or getattr(_actor_obj, `"id`", None)"
    "${indent}if _actor_id not in {_initiator_id, _redeemer_id}:"
    "${indent2}raise HTTPException(status_code=403, detail=`"forbidden`")"
  )

  # insert right after assignment line
  $newLines = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Count; $i++) {
    $newLines.Add($lines[$i])
    if ($i -eq $assignIdx) {
      foreach ($g in $guard) { $newLines.Add($g) }
    }
  }

  WriteUtf8 $routerPath (JoinLines $newLines.ToArray() $nl)
  Info "OK: Router gepatcht: $routerPath"
  return $true
}

function PatchTests([string]$testPath) {
  $text = ReadUtf8 $testPath
  if ($text -match "ONLY_INITIATOR_OR_REDEEMER_TEST") {
    Info "OK: Tests bereits gepatcht (Marker gefunden)."
    return $false
  }

  $nl = DetectNewline $text
  $lines = SplitLines $text

  # find a line that calls status with tok_b (we patch within that test)
  $anchorIdx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '/sale/transfer/status/\{tid\}' -and $lines[$i] -match 'tok_b') {
      $anchorIdx = $i
      break
    }
  }
  if ($anchorIdx -lt 0) {
    Die "PATCH-ABBRUCH: Konnte im Test keine Status-Call-Zeile mit tok_b finden: $testPath"
  }

  # find surrounding test function
  $fnStart = -1
  for ($i=$anchorIdx; $i -ge 0; $i--) {
    if ($lines[$i] -match '^def\s+test_') { $fnStart = $i; break }
  }
  if ($fnStart -lt 0) {
    Die "PATCH-ABBRUCH: Konnte den Start der Testfunktion nicht finden (def test_*)."
  }

  $fnEnd = $lines.Count
  for ($i=$fnStart+1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^def\s+test_') { $fnEnd = $i; break }
  }

  # inside that function: insert before first redeem call
  $insertAt = -1
  for ($i=$fnStart; $i -lt $fnEnd; $i++) {
    if ($lines[$i] -match '"/sale/transfer/redeem"' -or $lines[$i] -match "'/sale/transfer/redeem'") {
      $insertAt = $i
      break
    }
  }
  if ($insertAt -lt 0) {
    Die "PATCH-ABBRUCH: Konnte im Zieltest keine Redeem-Call-Zeile finden."
  }

  # detect indentation from the redeem line
  $indentMatch = [regex]::Match($lines[$insertAt], '^(\s+)')
  $indent = "    "
  if ($indentMatch.Success) { $indent = $indentMatch.Groups[1].Value }

  $block = @(
    "${indent}# ONLY_INITIATOR_OR_REDEEMER_TEST: vor Redeem darf Nicht-Initiator keinen Status lesen (verhindert tid-Enumeration)"
    "${indent}rs_pre = client.get(f`"/sale/transfer/status/{tid}`", headers={`"Authorization`": f`"Bearer {tok_b}`"})"
    "${indent}assert rs_pre.status_code == 403, rs_pre.text"
    ""
  )

  $newLines = New-Object System.Collections.Generic.List[string]
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($i -eq $insertAt) {
      foreach ($b in $block) { $newLines.Add($b) }
    }
    $newLines.Add($lines[$i])
  }

  WriteUtf8 $testPath (JoinLines $newLines.ToArray() $nl)
  Info "OK: Tests gepatcht: $testPath"
  return $true
}

# --- main ---
$routerPath = Join-Path $RepoRoot "server/app/routers/sale_transfer.py"
$testPath   = Join-Path $RepoRoot "server/tests/test_sale_transfer_api.py"

if (-not (Test-Path $routerPath)) { Die "FEHLT: $routerPath" }
if (-not (Test-Path $testPath))   { Die "FEHLT: $testPath" }

$changedRouter = PatchRouter $routerPath
$changedTests  = PatchTests  $testPath

if (-not $changedRouter -and -not $changedTests) {
  Info "OK: Nichts zu tun (alles bereits gepatcht)."
} else {
  Info "DONE: Patch angewendet. Jetzt: git diff prüfen, committen, pytest."
}