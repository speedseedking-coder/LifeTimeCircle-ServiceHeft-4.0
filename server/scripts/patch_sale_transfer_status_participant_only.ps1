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

  # fallback: add separate import near top after first import line
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

  $new2 = @("from fastapi import HTTPException") + $lines
  Info "OK: HTTPException Import am Dateianfang ergänzt."
  return ,$new2
}

function CountChar([string]$s, [char]$c) {
  $n = 0
  foreach ($ch in $s.ToCharArray()) { if ($ch -eq $c) { $n++ } }
  return $n
}

function FindDecoratorBlock([string[]]$lines, [string]$method) {
  # returns @{ start = int; end = int; text = string; firstLine = string } or $null
  for ($i=0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($ln -match ("^\s*@\w+\." + [regex]::Escape($method) + "\s*\(")) {
      $depth = (CountChar $ln '(') - (CountChar $ln ')')
      $j = $i
      while ($depth -gt 0 -and ($j + 1) -lt $lines.Count) {
        $j++
        $depth += (CountChar $lines[$j] '(') - (CountChar $lines[$j] ')')
      }
      $block = $lines[$i..$j]
      $text = [string]::Join("`n", $block)
      return @{ start = $i; end = ($j + 1); text = $text; firstLine = $ln }
    }
  }
  return $null
}

function FindStatusEndpoint([string[]]$lines) {
  # 1) try: GET decorator block containing "status" anywhere in block
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*@\w+\.get\s*\(') {
      $depth = (CountChar $lines[$i] '(') - (CountChar $lines[$i] ')')
      $j = $i
      while ($depth -gt 0 -and ($j + 1) -lt $lines.Count) {
        $j++
        $depth += (CountChar $lines[$j] '(') - (CountChar $lines[$j] ')')
      }
      $block = $lines[$i..$j]
      $text = [string]::Join("`n", $block)
      if ($text -match 'status') {
        return @{ decorStart = $i; decorEnd = ($j + 1); decorText = $text }
      }
      $i = $j
    }
  }

  # 2) fallback: function name contains status
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*def\s+\w*status\w*\s*\(') {
      return @{ decorStart = -1; decorEnd = -1; decorText = "" ; defIndex = $i }
    }
  }

  return $null
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
    if ($ln.StartsWith($baseIndent) -and $ln -match '^\s*(def|@)\s+') {
      return $i
    }
  }
  return $lines.Count
}

function ExtractActorParamName([string[]]$lines, [int]$defIndex) {
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

function ExtractPathParamFromDecorText([string]$decorText) {
  # try to find first quoted path containing {param}
  $m = [regex]::Match($decorText, '["''](?<path>[^"'']+)["'']')
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

  $found = FindStatusEndpoint $lines
  if (-not $found) {
    # Debug-Hinweise (kurz, aber hilfreich)
    Info "HINT: In sale_transfer.py keine @*.get(...status...) Block gefunden."
    Info "HINT: Zeilen mit 'status' (zur Orientierung):"
    for ($k=0; $k -lt $lines.Count; $k++) {
      if ($lines[$k] -match 'status') { Info ("  L{0}: {1}" -f ($k+1), $lines[$k].Trim()) }
    }
    Die "PATCH-ABBRUCH: Status-Endpoint nicht gefunden (Decorator-Block oder def *status*)."
  }

  if ($found.ContainsKey("defIndex")) {
    $defIdx = [int]$found.defIndex
    $decorText = ""
    $paramName = "tid"
  } else {
    $decorStart = [int]$found.decorStart
    $decorEnd   = [int]$found.decorEnd
    $decorText  = [string]$found.decorText
    $defIdx = FindNextDefIndex $lines $decorEnd
    if ($defIdx -lt 0) { Die "PATCH-ABBRUCH: def nach Status-Decorator nicht gefunden in $routerPath." }
    $paramName = ExtractPathParamFromDecorText $decorText
  }

  $endIdx = FindFunctionEnd $lines $defIdx
  $actorName = ExtractActorParamName $lines $defIdx

  # find first assignment inside function body that references paramName; fallback to common candidates
  $cands = @($paramName, "tid", "transfer_id", "id") | Select-Object -Unique

  $assignIdx = -1
  $transferVar = $null
  for ($i=$defIdx+1; $i -lt $endIdx; $i++) {
    $ln = $lines[$i]
    if ($ln -match '^\s+\w+\s*=\s*' -and $ln.Contains("(")) {
      foreach ($c in $cands) {
        if ($ln -match ("\b" + [regex]::Escape($c) + "\b")) {
          $assignIdx = $i
          $m = [regex]::Match($ln, '^\s*(?<var>[A-Za-z_][A-Za-z0-9_]*)\s*=')
          if ($m.Success) { $transferVar = $m.Groups["var"].Value }
          break
        }
      }
      if ($assignIdx -ge 0) { break }
    }
  }

  if ($assignIdx -lt 0 -or -not $transferVar) {
    Die "PATCH-ABBRUCH: Konnte keine passende Fetch-Assignment-Zeile im Status-Endpoint finden (tid/transfer_id)."
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

  $fnStart = -1
  for ($i=$anchorIdx; $i -ge 0; $i--) {
    if ($lines[$i] -match '^\s*def\s+test_') { $fnStart = $i; break }
  }
  if ($fnStart -lt 0) {
    Die "PATCH-ABBRUCH: Konnte den Start der Testfunktion nicht finden (def test_*)."
  }

  $fnEnd = $lines.Count
  for ($i=$fnStart+1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*def\s+test_') { $fnEnd = $i; break }
  }

  $insertAt = -1
  for ($i=$fnStart; $i -lt $fnEnd; $i++) {
    if ($lines[$i] -match 'sale/transfer/redeem') {
      $insertAt = $i
      break
    }
  }
  if ($insertAt -lt 0) {
    Die "PATCH-ABBRUCH: Konnte im Zieltest keine Redeem-Call-Zeile finden."
  }

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