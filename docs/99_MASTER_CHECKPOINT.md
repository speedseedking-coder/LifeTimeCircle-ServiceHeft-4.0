# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-21** (Europe/Berlin)

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

### WIP: Encoding-Gate Determinismus (Mojibake Scan) (P0)
- Status: **WIP** (Branch: `fix/encoding-gitattributes`)
- Problem: Encoding-Gate war nicht deterministisch (wechselnde Treffer/Sortierung/Dateiangaben) -> Blind-Fixes/Loopings
- Fix-Strategie (P0):
  1) Deterministischer JSONL-Scanner als SoT: `tools/mojibake_scan.js`
  2) Report: `artifacts/mojibake_report.jsonl` (Records: `path,line,col,kind,match,snippet`)
  3) Phase 2: Fix **nur** auf gemeldete Stellen (kein global replace)
- Evidence (lokal):
  - Run: `node tools/mojibake_scan.js --root . > artifacts/mojibake_report.jsonl`
  - Treffer: **14**
  - Beispiele: `scripts/mojibake_scan.js` (Tooling mit Mojibake + ` `), `server/app/admin/routes.py` (Kommentar-Mojibake)
- Runbook (bindend): `docs/98_MOJIBAKE_DETERMINISTIC_SCAN_RUNBOOK.md`

### WIP: Vehicles MVP + Consent Gate (Next10 E2E)
- Status: **PR offen** (Branch: `$marker`)
- Scope:
  - `/vehicles` Router (Create/List/Get), object-level, Moderator überall 403 (außer Blog/News/Public)
  - VIN nur masked
  - `require_consent(db, actor)` Gate (deny-by-default, **403** `consent_required`)
  - Docs: Rights-Matrix korrigiert (Moderator strikt nur Blog/News; Consent/Profile/Support sonst 403)

---

## Aktueller Stand (main)

- Neu/aktualisiert: `docs/00_CODEX_CONTEXT.md` (Codex/Agent Briefing / SoT Helper)

✅ PR #122 **gemerged**: `fix(import): report hardening`
- Commit auf `main`: `f24a52e`
- Repo-Pfad-Cleanup (Windows): Repo-Root wieder korrekt und clean
- Docs aktualisiert: `docs/00_CODEX_CONTEXT.md`, `docs/04_REPO_STRUCTURE.md`, `docs/05_MAINTENANCE_RUNBOOK.md`

✅ PR #121 **gemerged**: `chore: add one-command test runner (backend+web)`
- Commit auf `main`: `8efc913`
- Neu: `tools/test_all.ps1` (One-Command Runner: backend+web)
- Updates: `.gitignore`, `README.md`, `docs/01_DECISIONS.md`

✅ PR #95 **gemerged**: `chore/ci-helper-script`
- `server/scripts/patch_ci_add_web_build_job.ps1` hinzugefügt (helper patch script, kein Workflow-Change)

✅ PR #94 **gemerged**: `chore/poetry-lock-py311`
- `server/poetry.lock` unter **Python 3.11** + `poetry 1.8.3` regeneriert; Tests grün

✅ PR #93 **gemerged**: `chore/add-master-checkpoint-patch-script`

✅ PR #89 gemerged: `chore(web): declare node engine >=20.19.0 (vite 7)`
- `packages/web/package.json`: `engines.node` auf **>=20.19.0** gesetzt (Vite 7 Requirement / verhindert lokale Mismatch-Setups)

✅ PR #87 gemerged: `chore(web): bump vite to 7.3.1 (esbuild GHSA-67mh-4wv8-2f99)`
- Fix dev-only Audit: esbuild Advisory GHSA-67mh-4wv8-2f99 (via Vite 7)
- Hinweis: Vite 7 benötigt Node.js >= 20.19

✅ PR #85 **gemerged** (Auto-Merge squash): `test(api): bypass vehicles consent dependency in vehicles/entries suite`
- Ziel: Vehicles/Entries Tests sollen **nicht** vom Consent-Accept-Flow abhängen (Consent wird separat getestet)
- Fix: Collect-time Crash (NameError) durch kaputte/teilweise Einfügungen rund um `_require_consent` beseitigt
- Files:
  - `server/tests/test_vehicles_entries_api_p0.py` (Consent-Token-Snippets entfernt; `_ensure_consent()` = No-Op)
  - `server/scripts/patch_vehicle_tests_bypass_consent_dependency_p0.ps1` (idempotent)
- Tests grün: `poetry run pytest -q`

✅ PR #83 **gemerged** (Squash): `CI Guard Conflict Fix (pytest job detection)`
- Fix: Conflict-Marker entfernt + Job-Name-Erkennung für `name: pytest` stabilisiert
- Lokal verifiziert:
  - `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ci_guard_required_job_pytest.ps1`
  - Output: `OK: CI Guard – required job 'pytest' ist vorhanden.`

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

✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`
- CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf
- Script: `server/scripts/patch_ci_fix_docs_validator_step.ps1`
- CI grün: **pytest** + Docs Unified Validator + Web Build (`packages/web`)

✅ PR #60 gemerged: `docs: unify final spec (userflow/trust/pii/modules/transfer/pdfs/notifications/import)`
- Neue SoT Datei: `docs/02_PRODUCT_SPEC_UNIFIED.md`
- Updates: `docs/01_DECISIONS.md`, `docs/03_RIGHTS_MATRIX.md`, `docs/04_REPO_STRUCTURE.md`, `docs/06_WORK_RULES.md`, `docs/99_MASTER_CHECKPOINT.md`
- Script: `server/scripts/patch_docs_unified_final_refresh.ps1` (Validator; idempotent; keine Änderungen an bestehenden Docs)

✅ PR #54: `fix(web): add mandatory Public QR disclaimer`
- Pflichttext ist exakt in `packages/web/src/pages/PublicQrPage.tsx`:
  - „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
- Script: `server/scripts/patch_public_qr_disclaimer.ps1` (idempotent)

✅ PR #53: `chore(web): add web smoke toolkit script`
- Script: `server/scripts/ltc_web_toolkit.ps1`
  - quiet kill-node
  - optional `-Clean`
  - `npm ci` + `npm run build`

✅ PR #57: `docs: master checkpoint 2026-02-06 (PR #53/#54)`
- Script: `server/scripts/patch_master_checkpoint_pr53_pr54.ps1` (idempotent)

✅ PR #58: `chore(web): silence npm cache clean --force warning (stderr redirect)`
- `server/scripts/ltc_web_toolkit.ps1` enthält:
  - `try { & cmd /c "npm cache clean --force" 2>$null | Out-Null } catch { }`
- Script: `server/scripts/patch_ltc_web_toolkit_silence_npm_cache_warn.ps1` (idempotent)

✅ PR #59: `docs: master checkpoint add PR #58`
- Script: `server/scripts/patch_master_checkpoint_pr58.ps1` (idempotent, UTF-8 no BOM)

✅ P0 Uploads-Quarantäne: Uploads werden **quarantined by default**, Approve nur nach Scan=**CLEAN**
✅ Fix Windows-SQLite-Locks: Connections sauber schließen (Tempdir/cleanup stabil)