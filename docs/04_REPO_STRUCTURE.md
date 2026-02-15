# docs/04_REPO_STRUCTURE.md
# LifeTimeCircle – Service Heft 4.0
**Repo-Struktur / Source of Truth (SoT)**  
Stand: **2026-02-08**

> Ziel: klare Pfade, keine Altversionen, keine Duplikate.  
> **./docs** ist Source of Truth.

---

## 1) Source of Truth (SoT)
- **./docs** ist SoT für: Architektur, Policy, RBAC, Workflow, Produkt-Spezifikation.
- Keine Altpfade/Altversionen (keine Kopien unter `server/` etc.).

---

## 2) Struktur (Soll-Stand)

LifeTimeCircle-ServiceHeft-4.0/
- docs/
  - 01_DECISIONS.md
  - 02_PRODUCT_SPEC_UNIFIED.md
  - 03_RIGHTS_MATRIX.md
  - 04_REPO_STRUCTURE.md
  - 06_WORK_RULES.md
  - 99_MASTER_CHECKPOINT.md
- server/
  - app/
    - main.py
    - routers/
    - services/
    - models/
    - auth/
  - tests/
  - scripts/
  - data/      (runtime)
  - storage/   (runtime)
- packages/
  - web/
    - src/
    - public/
    - index.html
    - vite.config.ts
- .github/
  - workflows/
    - ci.yml

---

## 3) Web-Frontend (packages/web)
- Vite + React + TypeScript
- Dev-URL: `http://127.0.0.1:5173`
- Proxy: `/api/*` → `http://127.0.0.1:8000/*`

---

## 4) CI / Workflow
- Workflows liegen in `.github/workflows/*.yml`
- Server-CI (Working-Directory `server/`):
  - `poetry install`
  - `poetry run pytest -q`
- Web-Build sollte zusätzlich in CI als eigener Job laufen (MVP-Härtung):
  - `cd packages/web`
  - `npm ci`
  - `npm run build`

---

## 5) Runtime-Verzeichnisse (nicht versionieren)
- `server/data/` (SQLite DB)
- `server/storage/` (Uploads)
- `packages/web/dist/`, `packages/web/node_modules/`, `packages/web/.vite/`

---

## 6) Quick Commands (Windows / Repo-Root)
```powershell
cd (git rev-parse --show-toplevel)

# Sync + Status
git switch main
git pull --ff-only origin main
git status -sb

# Server Tests
cd .\server
$env:LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
poetry run pytest -q
py -3.11 -m poetry run pytest -q

# Web Smoke (build)
cd ..
pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_web_toolkit.ps1 -Smoke -Clean
