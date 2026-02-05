# LifeTimeCircle – Service Heft 4.0
**Repo-Struktur / Source of Truth (SoT)**  
Stand: 2026-02-05

> Ziel: klare Pfade, keine Altversionen, keine Duplikate.

---

## 1. Source of Truth
- **./docs** ist SoT für Architektur/Policy/RBAC/Workflow.
- Keine “alten” Docs-Pfade (keine Kopien unter server/ etc.).

---

## 2. Struktur

LifeTimeCircle-ServiceHeft-4.0/
docs/
01_DECISIONS.md
03_RIGHTS_MATRIX.md
04_REPO_STRUCTURE.md
06_WORK_RULES.md
99_MASTER_CHECKPOINT.md
server/
app/
main.py
routers/
services/
models/
auth/
tests/
scripts/
data/ (runtime)
storage/ (runtime)
.github/
workflows/
ci.yml


---

## 3. CI / Workflow
- Workflows liegen in **Repo-Root**: `.github/workflows/*.yml`
- CI läuft im `server/` Working-Directory:
  - `poetry install`
  - `poetry run pytest -q`
  - runtime dirs vorbereiten: `mkdir -p data`

---

## 4. Runtime-Verzeichnisse (nicht versionieren)
- `server/data/` (SQLite DB)
- `server/storage/` (Uploads)

---

## 5. Quick Commands
```powershell
# Root
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

# Status
git status