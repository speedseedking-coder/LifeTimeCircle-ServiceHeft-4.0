# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-24** (Europe/Berlin)

Projekt:
- Brand: **LifeTimeCircle**
- Modul: **Service Heft 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

---

## Produkt-Spezifikation (Unified) — SoT
- **Ab jetzt nur noch „LifeTimeCircle · Service Heft (Unified)“** (kein Parallelzweig „2.0“)
- Vollständige Spezifikation: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Spezifikation ist erweitert/finalisiert (E2E-Flow, Trust/Unfalltrust, PII, Module, Transfer/Dealer, PDFs/TTL, Notifications, Import, Packaging) – siehe `docs/02_PRODUCT_SPEC_UNIFIED.md`

---

## WIP / Offene PRs / Branch-Stand (nicht main)

### WIP: NEXT-BLOCK nach P0 — Frontend App-Shell (Auth/Consent/RBAC-Navigation)
- Status: **IN REVIEW (pending green)**
- Scope (SoT):
  - Web-App Shell für produktiven Einstiegspfad (Login → Consent → geschützte Bereiche) gemäß `docs/02_PRODUCT_SPEC_UNIFIED.md`
  - Serverseitige Security bleibt führend: deny-by-default, RBAC + object-level checks, Moderator nur Blog/News
  - UI zeigt nur zulässige Navigation; Enforcement bleibt ausschließlich Backend
- DoD (minimal, deterministisch):
  - Routing/Guards: 401 → Auth, `consent_required` → Consent, 403 sauber dargestellt
  - Keine PII/Secrets in UI-Logs/Responses/Telemetry
  - Pflichttext Public-QR bleibt exakt unverändert
  - `tools/test_all.ps1` und `tools/ist_check.ps1` grün
- Evidence:
  - Branch: `fix/web-app-shell-auth-header-gating-p1b`
  - PR: #210
  - Commits:
    - a27d6b4 fix(web): ts guard for consent_required code
    - a0bf2f2 fix(web): auth header gating + consent/RBAC hardening (P1)
  - Tests lokal:
    - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1` ✅
    - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1` ✅

### WIP: NEXT-BLOCK nach P1 — Web Consent-Drift Hardening (consent_required tolerant)
- Status: **OPEN**
- Scope:
  - Web akzeptiert `consent_required` als String ODER als Objekt-Shape (z. B. `detail.code`)
  - Keine Backend-Änderung; serverseitige Enforcement bleibt führend (deny-by-default)
- DoD (lokal Windows):
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1` ✅ (ALL GREEN)
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1` ✅
- Evidence:
  - Branch: `fix/vehicles-consent-moderator-next10`
  - PR: #212
  - Note [PR-212-NOOP]: PR #212 ist stale/no-op: verbleibender Diff entfernt export isConsentRequired und bricht den Web-Build; PR schließen/ignorieren.
  - Commit: 5b68eb5 — `fix(web): accept consent_required shapes (string or detail.code)`

✅ PR (pending): `feat(trust): add deterministic trust codes + public qr mapping (safe v1)`
- Neu: `server/app/services/trust_codes_v1.py` (Reason-Codes, Prioritaeten, Catalog-Validation, VIP Top-N)
- Neu: `server/app/services/trust_light_v1.py` (Severity->Ampel, deterministischer Public-Hint, Gruen-Fallback)
- Public-QR nutzt jetzt deterministische Codes statt Inline-Hardcode; Verhalten bleibt fuer v1 stabil (`gelb` + gleicher Hint).
- Tests: `server/tests/test_trust_codes_v1_catalog.py`, `server/tests/test_trust_light_v1.py`
- Security/Policy: no-PII Hints, keine Ziffern in Public-Hints, Moderator auf `/public/*` weiterhin `403` via Guard.

## Aktueller Stand (main)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #211 gemerged: test(api): next10 moderator public + vehicles consent runtime coverage
- Commit: 4cd0203
- Neu: `server/tests/test_next10_moderator_public_and_vehicles.py`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #203 gemerged: tools(verify): add P0 mojibake/Next10 verify runner
- Commit: cb42be2
- Neu: server/scripts/ltc_verify_p0_mojibake_next10.ps1
- Lokal verifiziert auf main:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 → **ALL GREEN ✅**
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1 → **grün**
  - Web E2E (Playwright Mini): 4/4 (401→#/auth, Loop-Guard, 403 consent_required→#/consent, Public-QR Disclaimer dedupe+exakt)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #202 gemerged: fix(encoding): make mojibake gate deterministic (JSONL scanner as SoT)
- Commit: f68ba25
- CI: Job pytest enthält Gate
  - `node tools/mojibake_scan.js --root .` (deterministisch, Exit 0/1)

✅ fix(docs/tests): Moderator-Allowlist konsistent zu Policy (nur /auth + /blog + /news; Moderator bekommt 403 auf /public und /health)
- Neu/aktualisiert: `docs/00_CODEX_CONTEXT.md` (Codex/Agent Briefing / SoT Helper)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #189 gemerged: chore(tests): replace deprecated datetime.utcnow with timezone-aware now
- Commit auf main: ee02b8e
- Fix: entfernt DeprecationWarning (utcnow) im Export-P0 Test

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #188 gemerged: fix(export): vehicle P0 export shape + persistent grants table (id PK) + one-time token
- Commit auf main: db023ec
- Server: server/app/routers/export_vehicle.py (RBAC + Redaction + Grants persistence + Encryption)
- Tests: server/tests/test_export_vehicle_p0.py
- Behavior:
  - GET /export/vehicle/{id} → { "data": ... } inkl. data["_redacted"]=true, vin_hmac, **kein** VIN/owner_email Leak
  - POST /export/vehicle/{id}/grant → persistente DB-Tabelle export_grants_vehicle (id PK, export_token unique, expires_at, used, created_at)
  - GET /export/vehicle/{id}/full → Header X-Export-Token (400 wenn fehlt), **one-time** + **TTL**, decrypted payload enthält payload["vehicle"]["vin"] (+ data.vehicle für P0-Kompat)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #171 **gemerged**: `fix(encoding): repair mojibake in rbac.py comments`
- Fix: `server/app/rbac.py` Kommentar-Encoding repariert (Beispiel-Codepoints: U+00C3 U+00BC, U+00C3 U+00A4)
- Gate wieder grün: `tools/test_all.ps1` → **ALL GREEN**
- CI Checks: **2 checks passed**

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #170 **gemerged**: `feat(security): add no-PII security telemetry (audit events + redaction + request id)`
- Commit auf `main`: `e9f0fdb`
- Neue Module:
  - `server/app/security/telemetry.py`
  - `server/app/security/redaction.py`
  - `server/app/security/request_id.py`
  - `server/app/security/__init__.py`
- Integration:
  - Middleware: `RequestIdMiddleware`
  - Status -> Event Mapping (`map_status_to_event`)
  - zentrale Event-Emission (`emit_security_event`)
- Policy:
  - strikt **no-PII**
  - Redaction verpflichtend
  - Request-ID erlaubt zur technischen Korrelation
- Tests:
  - `server/tests/test_security_telemetry.py`
  - `pytest` grün
- Lokal verifiziert:
  - `tools/test_all.ps1` → **ALL GREEN**

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #122 **gemerged**: `fix(import): report hardening`
- Commit auf `main`: `f24a52e`
- Repo-Pfad-Cleanup (Windows): Repo-Root wieder korrekt und clean
- Docs aktualisiert: `docs/00_CODEX_CONTEXT.md`, `docs/04_REPO_STRUCTURE.md`, `docs/05_MAINTENANCE_RUNBOOK.md`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #121 **gemerged**: `chore: add one-command test runner (backend+web)`
- Commit auf `main`: `8efc913`
- Neu: `tools/test_all.ps1` (One-Command Runner: backend+web)
- Updates: `.gitignore`, `README.md`, `docs/01_DECISIONS.md`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #95 **gemerged**: `chore/ci-helper-script`
- `server/scripts/patch_ci_add_web_build_job.ps1` hinzugefügt (helper patch script, kein Workflow-Change)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #94 **gemerged**: `chore/poetry-lock-py311`
- `server/poetry.lock` unter **Python 3.11** + `poetry 1.8.3` regeneriert; Tests grün

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #93 **gemerged**: `chore/add-master-checkpoint-patch-script`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #89 gemerged: `chore(web): declare node engine >=20.19.0 (vite 7)`
- `packages/web/package.json`: `engines.node` auf **>=20.19.0** gesetzt (Vite 7 Requirement / verhindert lokale Mismatch-Setups)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #87 gemerged: `chore(web): bump vite to 7.3.1 (esbuild GHSA-67mh-4wv8-2f99)`
- Fix dev-only Audit: esbuild Advisory GHSA-67mh-4wv8-2f99 (via Vite 7)
- Hinweis: Vite 7 benötigt Node.js >= 20.19

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #85 **gemerged** (Auto-Merge squash): `test(api): bypass vehicles consent dependency in vehicles/entries suite`
- Ziel: Vehicles/Entries Tests sollen **nicht** vom Consent-Accept-Flow abhängen (Consent wird separat getestet)
- Fix: Collect-time Crash (NameError) durch kaputte/teilweise Einfügungen rund um `_require_consent` beseitigt
- Files:
  - `server/tests/test_vehicles_entries_api_p0.py` (Consent-Token-Snippets entfernt; `_ensure_consent()` = No-Op)
  - `server/scripts/patch_vehicle_tests_bypass_consent_dependency_p0.ps1` (idempotent)
- Tests grün: `poetry run pytest -q`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #83 **gemerged** (Squash): `CI Guard Conflict Fix (pytest job detection)`
- Fix: Conflict-Marker entfernt + Job-Name-Erkennung für `name: pytest` stabilisiert
- Lokal verifiziert:
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ci_guard_required_job_pytest.ps1`
  - Output: `OK: CI Guard – required job 'pytest' ist vorhanden.`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #75 **gemerged** (Auto-Merge squash): `Docs: CI context + UTF-8 encoding fix (SoT)`
- Fix für Mojibake/UTF-8 in SoT-Dokumenten:
  - `docs/99_MASTER_CHECKPOINT.md`
  - `docs/01_DECISIONS.md`
- Script:
  - `server/scripts/fix_docs_encoding_utf8.ps1` (byte-level repair, UTF-8 safe)
- Branch Protection nachhaltig gefixt:
  - Required status check = **Job-Name `pytest`**
  - Verifikation via Check-Runs:
    - `gh api "repos/$repo/commits/$sha/check-runs" --jq ".check_runs[].name"`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`
- CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf
- Script: `server/scripts/patch_ci_fix_docs_validator_step.ps1`
- CI grün: **pytest** + Docs Unified Validator + Web Build (`packages/web`)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #60 gemerged: `docs: unify final spec (userflow/trust/pii/modules/transfer/pdfs/notifications/import)`
- Neue SoT Datei: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Updates: `docs/01_DECISIONS.md`, `docs/03_RIGHTS_MATRIX.md`, `docs/04_REPO_STRUCTURE.md`, `docs/06_WORK_RULES.md`, `docs/99_MASTER_CHECKPOINT.md`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` (Validator; idempotent; keine Änderungen an bestehenden Docs)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #54: `fix(web): add mandatory Public QR disclaimer`
- Pflichttext ist exakt in `packages/web/src/pages/PublicQrPage.tsx`:
  - „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
- Script: `server/scripts/patch_public_qr_disclaimer.ps1` (idempotent)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #53: `chore(web): add web smoke toolkit script`
- Script: `server/scripts/ltc_web_toolkit.ps1`
  - quiet kill-node
  - optional `-Clean`
  - `npm ci` + `npm run build`

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #57: `docs: master checkpoint 2026-02-06 (PR #53/#54)`
- Script: `server/scripts/patch_master_checkpoint_pr53_pr54.ps1` (idempotent)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #58: `chore(web): silence npm cache clean --force warning (stderr redirect)`
- `server/scripts/ltc_web_toolkit.ps1` enthält:
  - `try { & cmd /c "npm cache clean --force" 2>$null | Out-Null } catch { }`
- Script: `server/scripts/patch_ltc_web_toolkit_silence_npm_cache_warn.ps1` (idempotent, UTF-8 no BOM)

✅ PR #232 **gemerged**: eat(trust): trust folders CRUD + addon gate (grandfathering)
- Backend: /trust/folders/* CRUD-light, **consent-gated**
- Add-on Gate: Decisions **D-012/D-028**, **deny-by-default** + Legacy-Backfill (grandfathered)
- Security: **Object-Level Owner/Admin**, Moderator überall **403**
- Tests: server/tests/test_trust_folders_addon_gate_p1.py
- Evidence lokal:
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1 ✅
  - pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1 ✅


✅ PR #59: `docs: master checkpoint add PR #58`
- Script: `server/scripts/patch_master_checkpoint_pr58.ps1` (idempotent, UTF-8 no BOM)

✅ P0 Uploads-Quarantäne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**
✅ Fix Windows-SQLite-Locks: Connections sauber schließen (Tempdir/cleanup stabil)

---

### WIP: NEXT-BLOCK — gestartet (Branch: feat/next-block-pr79-followup)
- Ziel: Next Block nach PR79 (SoT-first, deny-by-default)
- DoD: tools/test_all.ps1 ALL GREEN ✅
- Hinweis: PR wird erst erstellt, sobald mindestens 1 Commit vom main abweicht.

