
```md
# docs/04_REPO_STRUCTURE.md
# LifeTimeCircle – Service Heft 4.0
**Repo-Struktur / Source of Truth (SoT)**  
Stand: 2026-02-06

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
07_MVP_DONE.md
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
packages/
web/
(React+Vite, lokal, optional)
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
- `packages/web/node_modules/`
- `packages/web/dist/`
- `packages/web/.vite/`

---

## 5. Quick Commands
```powershell
# Root
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

# Status
git status

# API (Backend)
cd ".\server"
$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
poetry run uvicorn app.main:app --reload

# Web (Frontend)
cd "..\packages\web"
npm install
npm run dev