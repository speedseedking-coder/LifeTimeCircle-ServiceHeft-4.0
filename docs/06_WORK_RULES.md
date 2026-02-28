# LifeTimeCircle – Service Heft 4.0
**Arbeitsregeln / Engineering-Disziplin**

Stand: 2026-02-21

---

## 1. Source of Truth

- ./docs ist SoT
- Keine Parallel-Spezifikationen
- Produkt-Spec bindend: docs/02_PRODUCT_SPEC_UNIFIED.md
- Entscheidungen: docs/01_DECISIONS.md
- Rechte: docs/03_RIGHTS_MATRIX.md
- Checkpoint: docs/99_MASTER_CHECKPOINT.md

---

## 2. Security Default

- deny-by-default
- least privilege
- RBAC serverseitig enforced
- Object-Level Checks verpflichtend
- Moderator strikt nur Blog/News
- Keine PII in Logs, Exports oder Telemetry

---

## 3. PR-Disziplin

PR gilt als fertig nur wenn:

1. Required Check `pytest` ist grün
2. tools/test_all.ps1 ist lokal grün
3. Encoding-Gate ist grün
4. Docs wurden angepasst, falls:
   - neue Policy
   - neue Route
   - neues Security-Verhalten
   - neue Rolle/Rechte

---

## 4. Encoding-Regeln

- UTF-8 only
- Kein BOM
- Mojibake-Fixes nur auf gemeldete Stellen
- Scanner SoT: tools/mojibake_scan.js
- Default-Scan (CI/Gate): **tracked-only** (git ls-files) – untracked lokale Dateien (artifacts/, fixtures) brechen das Gate nicht mehr.
- Vollscan lokal (inkl. untracked): `node tools/mojibake_scan.js --root . --all-files`
- Deterministischer JSONL-Output

---

## 5. Telemetry-Regeln

- Strict no-PII
- Redaction vor Event-Emission
- Request-ID erlaubt
- Neue Felder nur nach explizierter SoT-Entscheidung

---

## 6. Protected Branch

- main ist geschützt
- Änderungen nur via PR
- Required Check: pytest
- CI Guard verhindert Job-Rename

---

## 7. Fix-Policy

- Kein global replace
- Keine Blind-Fixes
- Nur exakt gemeldete Stellen korrigieren
- Bei Gate-Fail: STOP → Analyse → gezielter Fix

---

## 8. Lokal-Standard-Run

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1
```

---

## 9. PowerShell Param-Gate

- In jeder `*.ps1` muss `param(...)` am Script-Anfang stehen.
- Erlaubt vor `param(...)`: Kommentare, `#requires`, `using`, Script-Attribute.
- Nicht erlaubt vor `param(...)`: Executable Code (führt zu Gate-Fail).
- Repo-weite Prüfung läuft über `tools/ps_param_gate.ps1` und ist in `tools/test_all.ps1` enthalten.
- Lokal schneller Check: `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ps_param_gate.ps1`

## Public-QR Pflichttext (exakt, unverändert)

Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.
