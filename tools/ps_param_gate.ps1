#requires -Version 7.0
<#
PowerShell Param-at-Top Gate (repo-wide)

Regel:
- Wenn ein .ps1 einen Script-level ParamBlock hat (AST: ScriptAst.ParamBlock),
  muss er "am Anfang" stehen.
- Vor dem Script-Param sind nur erlaubt:
  - Kommentare / Leerzeilen
  - #requires
  - using ...
  - einzeilige Script-Attribute wie [CmdletBinding(...)]

Wichtig:
- Function-Paramblöcke werden NICHT geprüft.
- Mispositioniertes param(...) wird erkannt, wenn es als top-level Command geparst wird.
#>

[CmdletBinding()]
param(
  [string[]]$Roots = @("tools", "server/scripts"),
  [string[]]$Exclude = @("tools/archive"),
  [string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Resolve-RepoRoot {
  try {
    $root = (& git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $root) { return $root.Trim() }
  } catch { }
  return (Resolve-Path ".").Path
}

$repoRoot = Resolve-RepoRoot
$repoRootNorm = ($repoRoot -replace '\\','/').TrimEnd('/')

function To-RelPath([string]$fullPath) {
  $p = ($fullPath -replace '\\','/')
  if ($p.StartsWith($repoRootNorm + "/")) { return $p.Substring($repoRootNorm.Length + 1) }
  return $p
}

function Is-ExcludedRel([string]$relPath) {
  $r = ($relPath -replace '\\','/').Trim('/')
  $probe = "/" + $r + "/"

  # harte Segment-Excludes (immer)
  if ($probe.Contains("/.git/")) { return $true }
  if ($probe.Contains("/node_modules/")) { return $true }
  if ($probe.Contains("/dist/")) { return $true }

  foreach ($ex in $Exclude) {
    if (-not $ex) { continue }
    $exNorm = ($ex -replace '\\','/').Trim('/')
    if ($exNorm.Length -eq 0) { continue }
    if ($r -eq $exNorm) { return $true }
    if ($r.StartsWith($exNorm + "/")) { return $true }
  }

  return $false
}

function Is-InsideFunction([System.Management.Automation.Language.Ast]$node) {
  $cur = $node.Parent
  while ($null -ne $cur) {
    if ($cur -is [System.Management.Automation.Language.FunctionDefinitionAst]) { return $true }
    $cur = $cur.Parent
  }
  return $false
}

function Assert-AllowedBeforeParam {
  param(
    [Parameter(Mandatory=$true)][string]$FullPath,
    [Parameter(Mandatory=$true)][string]$RelPath,
    [Parameter(Mandatory=$true)][int]$ParamStartLineNumber
  )

  $lines = [System.IO.File]::ReadAllLines($FullPath, [System.Text.Encoding]::UTF8)  # garantiert string[]
  $inBlockComment = $false

  for ($i = 1; $i -lt $ParamStartLineNumber; $i++) {
    $line = $lines[$i - 1]
    $t = $line.Trim()

    if ($inBlockComment) {
      if ($t -match '#>') { $inBlockComment = $false }
      continue
    }

    if ($t.Length -eq 0) { continue }        # leer
    if ($t.StartsWith("<#")) {               # block comment start
      if (-not ($t -match '#>')) { $inBlockComment = $true }
      continue
    }
    if ($t.StartsWith("#")) { continue }     # Kommentare / #requires

    if ($t -match '^(?i)#requires\b') { continue }
    if ($t -match '^(?i)using\s+') { continue }

    # einzeilige Script-Attribute (z.B. [CmdletBinding()] / [Diagnostics.CodeAnalysis.SuppressMessage(...)] )
    if ($t -match '^\[[A-Za-z_][A-Za-z0-9_.]*(\s*\(.*\))?\]\s*$') { continue }

    throw ("FAIL: {0}:{1} -> '{2}' (nur comments/#requires/using/attribute vor param erlaubt)" -f $RelPath, $i, $line.Trim())
  }
}

function Check-File([string]$fullPath) {
  $rel = To-RelPath $fullPath
  if (Is-ExcludedRel $rel) { return $false }

  # schneller Kandidatenfilter (sonst parse ich alles)
  $raw = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
  if ($raw -notmatch '(?i)\bparam\s*\(') { return $false }

  $tokens = $null
  $errors = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($fullPath, [ref]$tokens, [ref]$errors)

  if ($errors -and $errors.Count -gt 0) {
    $e = $errors[0]
    throw ("FAIL: parse error in {0} at {1}:{2} — {3}" -f $rel, $e.Extent.StartLineNumber, $e.Extent.StartColumnNumber, $e.Message)
  }

  if ($null -ne $ast.ParamBlock) {
    Assert-AllowedBeforeParam -FullPath $fullPath -RelPath $rel -ParamStartLineNumber $ast.ParamBlock.Extent.StartLineNumber
    Write-Host ("OK: {0}" -f $rel)
    return $true
  }

  # kein Script-ParamBlock: nur FAIL, wenn "param" als top-level Command geparst wird (kaputt positioniert)
  $paramCmd = $ast.Find(
    {
      param($node)
      if ($node -is [System.Management.Automation.Language.CommandAst]) {
        $name = $node.GetCommandName()
        if ($name -and $name.ToLowerInvariant() -eq 'param') {
          return -not (Is-InsideFunction $node)
        }
      }
      return $false
    },
    $true
  )

  if ($null -ne $paramCmd) {
    $lineNo = $paramCmd.Extent.StartLineNumber
    $lines2 = [System.IO.File]::ReadAllLines($fullPath, [System.Text.Encoding]::UTF8)
    $foundLine = if ($lineNo -ge 1 -and $lineNo -le $lines2.Count) { $lines2[$lineNo - 1] } else { "" }
    throw ("FAIL: {0}:{1} -> '{2}' (param wird als Command geparst; param-block ist nicht am Anfang)" -f $rel, $lineNo, $foundLine.Trim())
  }

  return $false
}

Set-Location $repoRoot
[Environment]::CurrentDirectory = $repoRoot

Write-Host ""
Write-Host "==> PowerShell param gate"

$files = New-Object System.Collections.Generic.List[string]

if ($Paths -and $Paths.Count -gt 0) {
  foreach ($p in $Paths) {
    if (-not $p) { continue }
    $abs = $p
    if (-not [System.IO.Path]::IsPathRooted($abs)) { $abs = Join-Path $repoRoot $p }
    if (-not (Test-Path -LiteralPath $abs)) { throw "Path not found: $p" }

    $item = Get-Item -LiteralPath $abs
    if ($item.PSIsContainer) {
      Get-ChildItem -LiteralPath $item.FullName -Recurse -File -Filter "*.ps1" | ForEach-Object { $files.Add($_.FullName) }
    } else {
      if ($item.FullName.ToLowerInvariant().EndsWith(".ps1")) { $files.Add($item.FullName) }
    }
  }
} else {
  foreach ($r in $Roots) {
    if (-not $r) { continue }
    $absRoot = $r
    if (-not [System.IO.Path]::IsPathRooted($absRoot)) { $absRoot = Join-Path $repoRoot $r }
    if (-not (Test-Path -LiteralPath $absRoot)) { continue }
    Get-ChildItem -LiteralPath $absRoot -Recurse -File -Filter "*.ps1" | ForEach-Object { $files.Add($_.FullName) }
  }
}

$filesSorted = $files | Sort-Object { To-RelPath $_ }

$checkedAny = $false
foreach ($f in $filesSorted) {
  $checked = Check-File -fullPath $f
  if ($checked) { $checkedAny = $true }
}

if (-not $checkedAny) {
  Write-Host "OK: no script-level param blocks found in scanned roots/paths."
}

