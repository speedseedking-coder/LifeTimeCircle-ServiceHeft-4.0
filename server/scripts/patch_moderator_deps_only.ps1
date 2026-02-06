# server/scripts/patch_moderator_deps_only.ps1
<#
P1: Moderator strikt nur Blog/News (kein Export, kein Audit-Read, keine PII)

Deps-only:
- Patcht NUR app/routers/**/*.py
- Fasst NIE an: auth.py, public_qr.py, news.py, blog.py
- Setzt dependencies=[Depends(forbid_moderator)] an APIRouter(...),
  wenn prefix NICHT in Allowlist ist.
- KEINE Import-Änderungen hier (die macht Fix-Skript).
#>

param([switch]$WhatIf)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }
function Warn($m){ Write-Host "WARN: $m" -ForegroundColor Yellow }

$serverRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$routerDir  = Join-Path $serverRoot "app\routers"
if (-not (Test-Path $routerDir)) { throw "routers/ nicht gefunden: $routerDir" }

$skipFiles = @("auth.py","public_qr.py","news.py","blog.py")

$allowPrefixes = @(
  "/news",
  "/blog",
  "/admin/news",
  "/admin/blog",
  "/auth",
  "/public",
  "/qr",
  "/docs",
  "/openapi",
  "/redoc"
)

function StartsWithAny([string]$s, [string[]]$prefixes) {
  foreach ($p in $prefixes) { if ($s.StartsWith($p)) { return $true } }
  return $false
}

function Find-MatchingDelimiter([string]$s, [int]$openIdx, [char]$openChar, [char]$closeChar) {
  $depth = 0
  $inSingle = $false
  $inDouble = $false
  $escape = $false

  for ($i = $openIdx; $i -lt $s.Length; $i++) {
    $ch = $s[$i]

    if ($escape) { $escape = $false; continue }
    if ($ch -eq '\') { $escape = $true; continue }

    if (-not $inDouble -and $ch -eq "'") { $inSingle = -not $inSingle; continue }
    if (-not $inSingle -and $ch -eq '"') { $inDouble = -not $inDouble; continue }

    if ($inSingle -or $inDouble) { continue }

    if ($ch -eq $openChar) { $depth++ ; continue }
    if ($ch -eq $closeChar) {
      $depth--
      if ($depth -eq 0) { return $i }
    }
  }
  return -1
}

function Patch-ApiRouterDependencies([string]$text) {
  $changed = $false
  $idx = 0

  while ($true) {
    $start = $text.IndexOf("APIRouter(", $idx)
    if ($start -lt 0) { break }

    $openParen = $start + "APIRouter".Length
    if ($openParen -ge $text.Length -or $text[$openParen] -ne "(") {
      $idx = $start + 1
      continue
    }

    $closeParen = Find-MatchingDelimiter $text $openParen '(' ')'
    if ($closeParen -lt 0) { break }

    $args = $text.Substring($openParen + 1, $closeParen - $openParen - 1)

    $mPrefix = [regex]::Match(
      $args,
      'prefix\s*=\s*["''](?<p>[^"''\r\n]+)["'']',
      [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if ($mPrefix.Success) {
      $prefix = $mPrefix.Groups["p"].Value
      if (StartsWithAny $prefix $allowPrefixes) {
        $idx = $closeParen + 1
        continue
      }
    } else {
      # Ohne prefix= nicht anfassen (minimiert Risiko)
      $idx = $closeParen + 1
      continue
    }

    if ($args -match '\bDepends\s*\(\s*forbid_moderator\s*\)') {
      $idx = $closeParen + 1
      continue
    }

    $newArgs = $args
    if ($newArgs -match '\bdependencies\s*=') {
      $brOpen = $newArgs.IndexOf("[")
      if ($brOpen -ge 0) {
        $brClose = Find-MatchingDelimiter $newArgs $brOpen '[' ']'
        if ($brClose -ge 0) {
          $inner = $newArgs.Substring($brOpen + 1, $brClose - $brOpen - 1).Trim()
          $insert = if ([string]::IsNullOrWhiteSpace($inner)) { "Depends(forbid_moderator)" } else { ", Depends(forbid_moderator)" }
          $newArgs = $newArgs.Substring(0, $brClose) + $insert + $newArgs.Substring($brClose)
        } else {
          $newArgs = $newArgs.TrimEnd()
          if (-not $newArgs.EndsWith(",")) { $newArgs += "," }
          $newArgs += " dependencies=[Depends(forbid_moderator)]"
        }
      } else {
        $newArgs = $newArgs.TrimEnd()
        if (-not $newArgs.EndsWith(",")) { $newArgs += "," }
        $newArgs += " dependencies=[Depends(forbid_moderator)]"
      }
    } else {
      $newArgs = $newArgs.TrimEnd()
      if (-not $newArgs.EndsWith(",") -and -not [string]::IsNullOrWhiteSpace($newArgs)) { $newArgs += "," }
      $newArgs += " dependencies=[Depends(forbid_moderator)]"
    }

    if ($newArgs -ne $args) {
      $text = $text.Substring(0, $openParen + 1) + $newArgs + $text.Substring($closeParen)
      $changed = $true
      $idx = $openParen + 1 + $newArgs.Length + 1
      continue
    }

    $idx = $closeParen + 1
  }

  return @($text, $changed)
}

$files = Get-ChildItem -Path $routerDir -Recurse -Filter "*.py"
$patched = New-Object System.Collections.Generic.List[string]

foreach ($f in $files) {
  $name = $f.Name.ToLowerInvariant()
  if ($skipFiles -contains $name) { continue }

  $path = $f.FullName
  $orig = Get-Content -Path $path -Raw -Encoding UTF8
  if ($orig -notmatch 'APIRouter\s*\(') { continue }

  $res = Patch-ApiRouterDependencies $orig
  $new = $res[0]
  $did = [bool]$res[1]

  if ($did -and $new -ne $orig) {
    if ($WhatIf) {
      Write-Host "WHATIF: würde patchen: $path"
    } else {
      Set-Content -Path $path -Value $new -Encoding UTF8
      $patched.Add($path) | Out-Null
    }
  }
}

if ($patched.Count -gt 0) {
  Ok "Gepatchte Router-Dateien:"
  $patched | ForEach-Object { Write-Host " - $_" }
} else {
  Warn "Keine Router-Dateien gepatcht."
}

Ok "FERTIG ✅"
