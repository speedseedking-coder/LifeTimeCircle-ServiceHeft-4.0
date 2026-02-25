
---

PFAD: `server/scripts/install_paste_guard_profile.ps1`
```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Muss aus Repo-Root laufen (SoT-Guard)
$repoRoot = (Get-Location).Path
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "docs"))) {
    throw "Bitte aus dem Repo-Root ausführen (Ordner 'docs' nicht gefunden)."
}

# Lokales Profil (KEIN OneDrive)
$profilePath = Join-Path $HOME "Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
$profileDir = Split-Path -Parent $profilePath

if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$beginMarker = "# LTC_PASTE_GUARD_BEGIN"
$endMarker   = "# LTC_PASTE_GUARD_END"

$block = @"
# LTC_PASTE_GUARD_BEGIN
Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function prompt { "PS `$((Get-Location).Path)> " }

Set-PSReadLineOption -EditMode Windows
Set-PSReadLineKeyHandler -Chord Ctrl+Shift+V -ScriptBlock {
    `$raw = Get-Clipboard -Raw
    if (`$null -eq `$raw) { return }

    # Drop/strip lines that start with "PS ...> " (common prompt)
    `$lines = `$raw -split "`r?`n"
    `$clean = foreach (`$l in `$lines) {
        if (`$l -match '^\s*PS\s+.+?>\s*') { `$l -replace '^\s*PS\s+.+?>\s*','' } else { `$l }
    }

    [Microsoft.PowerShell.PSConsoleReadLine]::Insert((`$clean -join "`n"))
}
# LTC_PASTE_GUARD_END
"@

$current = Get-Content -LiteralPath $profilePath -Raw

$pattern = [regex]::Escape($beginMarker) + '.*?' + [regex]::Escape($endMarker)

if ($current -match $pattern) {
    $updated = [System.Text.RegularExpressions.Regex]::Replace(
        $current,
        $pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $block },
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )
} else {
    $needsNewline = ($current.Length -gt 0) -and (-not $current.EndsWith("`n"))
    $sep = if ($needsNewline) { "`n`n" } else { "" }
    $updated = $current + $sep + $block + "`n"
}

# WICHTIG: UTF-8 OHNE BOM erzwingen (Encoding-Gate)
Set-Content -LiteralPath $profilePath -Value $updated -Encoding utf8NoBOM

Write-Host "Paste-Guard installiert/aktualisiert: $profilePath"
Write-Host "pwsh neu starten"
Write-Host "Sofort-Test (Clipboard):"
Write-Host "PS C:\...> git status -sb"
Write-Host "PS C:\...> git log --oneline -5"
Write-Host "Einfügen per Ctrl+Shift+V -> Erwartung: nur Commands ohne Prompt"