\# docs/05\_MAINTENANCE\_RUNBOOK.md

\# LifeTimeCircle – Service Heft 4.0

\*\*Maintenance / Runbook (SoT)\*\*  

Stand: \*\*2026-02-07\*\* (Europe/Berlin)



Ziel: Jede Person kann Setup, CI, Debugging und Pflege zuverlässig durchführen.



---



\## 1) Source of Truth (SoT)

Immer zuerst:

\- docs/99\_MASTER\_CHECKPOINT.md

\- docs/02\_PRODUCT\_SPEC\_UNIFIED.md

\- docs/03\_RIGHTS\_MATRIX.md

\- docs/01\_DECISIONS.md

\- docs/06\_WORK\_RULES.md



---



\## 2) Voraussetzungen (lokal)

\- PowerShell 7.x (pwsh)

\- Python 3.11 + Poetry

\- Node.js 20.x + npm

\- Git + GitHub CLI (gh)



---



\## 3) Quickstart (Repo-Root)

```powershell

cd (git rev-parse --show-toplevel)

git switch main

git pull --ff-only origin main

git status -sb


