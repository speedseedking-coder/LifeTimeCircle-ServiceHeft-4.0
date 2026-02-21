\# Mojibake/Encoding – Deterministischer Scan + Fix-Runbook (P0)



Stand: \*\*2026-02-21\*\* · Scope: \*\*Encoding-Gate stabilisieren\*\* (Determinismus → reparierbar → CI ruhig)



\## Ziel



\- Das Encoding-/Mojibake-Gate ist \*\*deterministisch\*\*.

\- Jeder Treffer ist \*\*exakt lokalisierbar\*\* (`path + line + col`).

\- Fixes erfolgen \*\*nur\*\* auf gemeldete Stellen (kein global replace, kein Guessing).

\- Exit-Code haengt \*\*nur\*\* von Trefferanzahl ab.



\## Source of Truth



\- Scanner: `tools/mojibake\_scan.js`

\- Report: `artifacts/mojibake\_report.jsonl`

\- Decision: `docs/01\_DECISIONS.md` → \*\*D-032\*\*



\## Scanner-Contract (JSONL)



Jede Zeile im Report ist ein JSON-Objekt:



\- `path` (posix-relativ zum Repo-Root)

\- `line` (1-based)

\- `col` (1-based)

\- `kind` = `mojibake` | `replacement\_char`

\- `match` (kurzer Match-String)

\- `snippet` (gekürzt, max. 200 Zeichen)



Sortierung (stabil):



1\) `path`

2\) `line`

3\) `col`

4\) `kind`

5\) `match`



Exit-Code:



\- `0` = keine Treffer

\- `1` = Treffer vorhanden

\- alles andere = Fehler (Runner bricht hart ab)



\## Allowlist / Default-Exclude



Allowlist Extensions:



\- `.md`, `.ts`, `.tsx`, `.js`, `.py`



Default-Exclude (Segment-basiert):



\- `.git/`

\- `node\_modules/`

\- `dist/`

\- `server/scripts/`

\- `tools/`

\- weitere Build-Artefakte (z.B. `packages/web/dist`, `.vite`)



> Hinweis: `scripts/` (Alt-Tooling) darf bei Bedarf zusaetzlich ausgeschlossen werden, wenn dort obsolete Scanner/Artefakte liegen.



\## Phase 1 – Deterministischen Report erzeugen



\### Windows (PowerShell)



```powershell

$ErrorActionPreference="Stop"

\[Console]::OutputEncoding=\[System.Text.Encoding]::UTF8

$root=(git rev-parse --show-toplevel).Trim()

Set-Location $root

New-Item -ItemType Directory -Force -Path .\\artifacts | Out-Null



\& node .\\tools\\mojibake\_scan.js --root $root |

&nbsp; Out-File -FilePath .\\artifacts\\mojibake\_report.jsonl -Encoding utf8



$LASTEXITCODE

