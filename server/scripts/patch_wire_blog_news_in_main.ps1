# server/scripts/patch_wire_blog_news_in_main.ps1
param(
  [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Find-LastMatch([string]$Text, [string]$Pattern) {
  $re = [regex]::new($Pattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
  $m = $null
  foreach ($x in $re.Matches($Text)) { $m = $x }
  return $m
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
} else {
  $RepoRoot = (Resolve-Path $RepoRoot).Path
}

$mainPath    = Join-Path $RepoRoot "server\app\main.py"
$routersInit = Join-Path $RepoRoot "server\app\routers\__init__.py"

if (-not (Test-Path $mainPath)) { throw "main.py nicht gefunden: $mainPath" }

# app/routers als Package absichern (nicht überschreiben)
if (-not (Test-Path $routersInit)) {
  Write-FileUtf8NoBom -Path $routersInit -Content "# app.routers package`n"
}

$raw = Get-Content -Raw -Encoding UTF8 $mainPath

# Newline-Style merken
$nl = "`n"
if ($raw -match "`r`n") { $nl = "`r`n" }

# intern auf LF normalisieren
$txt = $raw -replace "`r`n", "`n"

# --- Imports: blog/news sicherstellen ---
$needBlogImport = -not ([regex]::IsMatch($txt, '(?m)^\s*from\s+app\.routers\s+import\s+.*\bblog\b'))
$needNewsImport = -not ([regex]::IsMatch($txt, '(?m)^\s*from\s+app\.routers\s+import\s+.*\bnews\b'))

$importsToAdd = New-Object System.Collections.Generic.List[string]
if ($needBlogImport) { $importsToAdd.Add("from app.routers import blog") }
if ($needNewsImport) { $importsToAdd.Add("from app.routers import news") }

if ($importsToAdd.Count -gt 0) {
  # bevorzugt: nach letztem "from app.routers import ..."
  $mRouters = Find-LastMatch $txt '(?m)^\s*from\s+app\.routers\s+import\s+.+$'
  $mAnyImp  = Find-LastMatch $txt '(?m)^\s*(from|import)\s+.+$'

  $insertPos = 0
  if ($mRouters -ne $null) {
    $lineEnd = $txt.IndexOf("`n", $mRouters.Index)
    if ($lineEnd -lt 0) { $insertPos = $txt.Length } else { $insertPos = $lineEnd + 1 }
  } elseif ($mAnyImp -ne $null) {
    $lineEnd = $txt.IndexOf("`n", $mAnyImp.Index)
    if ($lineEnd -lt 0) { $insertPos = $txt.Length } else { $insertPos = $lineEnd + 1 }
  }

  $block = ""
  foreach ($l in $importsToAdd) { $block += $l + "`n" }
  $block += "`n"

  $txt = $txt.Substring(0, $insertPos) + $block + $txt.Substring($insertPos)
}

# --- include_router: direkt vor erstem "return app" ---
$hasBlogInclude = [regex]::IsMatch($txt, '(?m)^\s*app\.include_router\(\s*blog\.router\s*\)\s*$')
$hasNewsInclude = [regex]::IsMatch($txt, '(?m)^\s*app\.include_router\(\s*news\.router\s*\)\s*$')

if (-not $hasBlogInclude -or -not $hasNewsInclude) {
  $mReturn = [regex]::Match($txt, '(?m)^(?<indent>\s*)return\s+app\s*(#.*)?$')
  if (-not $mReturn.Success) { throw "Konnte 'return app' nicht finden in $mainPath" }

  $indent = $mReturn.Groups["indent"].Value

  $ins = ""
  $ins += $indent + "# Blog/News (public)" + "`n"
  if (-not $hasBlogInclude) { $ins += $indent + "app.include_router(blog.router)" + "`n" }
  if (-not $hasNewsInclude) { $ins += $indent + "app.include_router(news.router)" + "`n" }
  $ins += "`n"

  $txt = $txt.Substring(0, $mReturn.Index) + $ins + $txt.Substring($mReturn.Index)
}

# zurückschreiben (ursprüngliche Newlines)
$out = $txt.TrimEnd() + "`n"
if ($nl -eq "`r`n") { $out = $out -replace "`n", "`r`n" }

Write-FileUtf8NoBom -Path $mainPath -Content $out
Write-Host "OK: main.py wired (blog/news import + include_router)."