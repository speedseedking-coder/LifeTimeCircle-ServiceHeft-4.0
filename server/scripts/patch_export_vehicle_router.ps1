# Patch/Fix: Export-Vehicle Router korrekt in app/main.py registrieren
# - behebt auch IndentationError (wenn include_router auf Top-Level gelandet ist)
#
# Ausführen in: server\
#   pwsh -ExecutionPolicy Bypass -File .\scripts\patch_export_vehicle_router.ps1

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$main = Join-Path $root "app\main.py"

if (!(Test-Path $main)) {
  Write-Error "Nicht gefunden: $main"
  exit 1
}

$content = Get-Content -Raw -Path $main
$nl = "`n"
if ($content -match "`r`n") { $nl = "`r`n" }

$importLine = "from app.routers.export_vehicle import router as export_vehicle_router"

# 1) Import ergänzen (falls fehlt)
if ($content -notmatch [regex]::Escape($importLine)) {
  # Nach letztem "from app.routers..." import einfügen, sonst nach letztem "from app..." import, sonst ganz oben.
  $rx1 = [regex]::new('(?m)^\s*from\s+app\.routers\..+$')
  $m1 = $rx1.Matches($content)
  if ($m1.Count -gt 0) {
    $last = $m1[$m1.Count - 1]
    $pos = $last.Index + $last.Length
    $content = $content.Insert($pos, "$nl$importLine")
  } else {
    $rx2 = [regex]::new('(?m)^\s*from\s+app\..+$')
    $m2 = $rx2.Matches($content)
    if ($m2.Count -gt 0) {
      $last = $m2[$m2.Count - 1]
      $pos = $last.Index + $last.Length
      $content = $content.Insert($pos, "$nl$importLine")
    } else {
      $content = "$importLine$nl$content"
    }
  }
}

# 2) Falsche/alte include_router Zeile entfernen (egal wo sie steht)
#    (diese Zeile hat dir das IndentationError erzeugt, wenn sie auf Top-Level stand)
$content = [regex]::Replace(
  $content,
  '(?m)^\s*app\.include_router\(export_vehicle_router\)\s*(\r?\n)?',
  '',
  1
)

# 3) include_router korrekt VOR "return app" innerhalb create_app() einfügen
$rxReturn = [regex]::new('(?m)^(?<indent>\s*)return\s+app\s*$')
$mReturn = $rxReturn.Match($content)

if ($mReturn.Success) {
  $indent = $mReturn.Groups['indent'].Value
  $includeLine = "${indent}app.include_router(export_vehicle_router)"

  # Falls aus irgendeinem Grund schon direkt davor vorhanden: nicht doppeln
  $blockStart = [Math]::Max(0, $mReturn.Index - 300)
  $preview = $content.Substring($blockStart, $mReturn.Index - $blockStart)
  if ($preview -notmatch [regex]::Escape($includeLine)) {
    $content = $content.Insert($mReturn.Index, "$includeLine$nl")
  }
} else {
  # Fallback: Wenn kein "return app" gefunden wird, ans Ende hängen (besser als nix)
  $content = $content.TrimEnd() + "${nl}app.include_router(export_vehicle_router)${nl}"
}

Set-Content -Path $main -Value $content -Encoding UTF8
Write-Host "OK: Router export_vehicle korrekt registriert (Indent-Fix inkl.) in $main"

