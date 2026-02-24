[CmdletBinding()]
param(
  [string]$Path = "packages/web/src/pages/PublicQrPage.tsx",
  [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Required = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path

function Resolve-RepoPath {
  param([Parameter(Mandatory=$true)][string]$p)
  if ([System.IO.Path]::IsPathRooted($p)) { return $p }
  return (Join-Path $RepoRoot $p)
}

function Read-Utf8NoBom {
  param([Parameter(Mandatory=$true)][string]$p)

  if (-not (Test-Path -LiteralPath $p)) { throw "File not found: $p" }

  [byte[]]$bytes = [System.IO.File]::ReadAllBytes($p)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    if ($bytes.Length -eq 3) { return "" }
    $bytes = $bytes[3..($bytes.Length-1)]
  }
  return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Write-Utf8NoBom {
  param(
    [Parameter(Mandatory=$true)][string]$p,
    [Parameter(Mandatory=$true)][string]$t
  )

  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($p, $t, $enc)
}

$Target = Resolve-RepoPath -p $Path
if (-not (Test-Path -LiteralPath $Target)) { throw "Target not found: $Target" }

$text = Read-Utf8NoBom -p $Target

if ($text.Contains($Required)) {
  Write-Host "OK: disclaimer already present."
  exit 0
}

if ($CheckOnly) {
  Write-Error "MISSING: required Public-QR disclaimer not found."
  exit 1
}

$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }

$reReturn = [regex]::new("return\s*\(", [System.Text.RegularExpressions.RegexOptions]::Multiline)
$m = $reReturn.Match($text)
if (-not $m.Success) { throw "No 'return(' found in $Target" }
$returnIdx = $m.Index

$closeIdx = $text.LastIndexOf(");", [System.StringComparison]::Ordinal)
if ($closeIdx -lt 0 -or $closeIdx -le $returnIdx) { throw "No final ');' found after return( in $Target" }

$blockLen = $closeIdx - $returnIdx
$block = $text.Substring($returnIdx, $blockLen)

$relInsert = $block.LastIndexOf("</", [System.StringComparison]::Ordinal)
if ($relInsert -lt 0) { throw "No closing tag '</' found inside return-block in $Target" }

$globalInsertIdx = $returnIdx + $relInsert

$lineStart = $text.LastIndexOf($nl, $globalInsertIdx)
if ($lineStart -lt 0) { $lineStart = 0 } else { $lineStart += $nl.Length }

$indent = ""
if ($globalInsertIdx -gt $lineStart) {
  $indent = $text.Substring($lineStart, $globalInsertIdx - $lineStart)
  if ($indent.Trim().Length -ne 0) { $indent = "" }
}

$childIndent = $indent + "  "

$snippetLines = @(
  "$indent<div data-testid=""public-qr-disclaimer"" className=""mt-6 rounded-lg border p-3 text-xs opacity-80"">"
  "$childIndent$Required"
  "$indent</div>"
  ""
)
$snippet = ($snippetLines -join $nl)

$text = $text.Insert($globalInsertIdx, $snippet + $nl)

Write-Utf8NoBom -p $Target -t $text

$after = Read-Utf8NoBom -p $Target
if (-not $after.Contains($Required)) { throw "Patch failed: disclaimer still missing after write." }

Write-Host "OK: inserted mandatory Public-QR disclaimer."
