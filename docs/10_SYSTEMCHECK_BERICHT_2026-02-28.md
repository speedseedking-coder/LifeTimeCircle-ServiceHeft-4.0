# Systemcheck-Bericht – LifeTimeCircle Service Heft 4.0

Stand: 2026-02-28
Repo: `C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0`

## 1. Verifizierter Arbeitsstand

- Aktueller Branch: `feat/web-final-trust-folder-flow`
- HEAD: `6bdaf54` (`docs(work_rules): add mandatory Public-QR disclaimer`)
- Git-Status: Working tree clean
- Remote-Status: Branch ist `ahead 1` gegen `origin/feat/web-final-trust-folder-flow`

Der lokale Stand entspricht damit nicht der gelieferten Übergabe-Referenz auf Branch `work` mit Commit `e386b2d`.

## 2. Abgleich mit der gelieferten Übergabe

### Aussage: Neues Dokument `docs/10_IST_STAND_CODEX_VSCODE.md` erstellt

Befund:
- Datei im aktuellen Repo-Stand nicht vorhanden
- Auch in der lokalen Git-Historie nicht nachweisbar (`git log --all -- docs/10_IST_STAND_CODEX_VSCODE.md` ohne Treffer)

Bewertung:
- Nicht verifizierbar
- Sehr wahrscheinlich stammt diese Aussage aus einem anderen Branch, einer anderen Worktree-Kopie oder einem nicht vorliegenden Commit

### Aussage: `docs/99_MASTER_CHECKPOINT.md` enthält explizite Referenz auf das neue IST-Stand-Dokument

Befund:
- In `docs/99_MASTER_CHECKPOINT.md` wurde keine Referenz auf `docs/10_IST_STAND_CODEX_VSCODE.md` gefunden
- Der aktuelle Inhalt des Master-Checkpoints trägt den Stand `2026-02-06`

Bewertung:
- Im aktuellen Arbeitsstand nicht erfüllt

### Aussage: Änderungen committed auf Branch `work` mit Commit `e386b2d`

Befund:
- Commit `e386b2d` ist lokal nicht vorhanden
- Ein Branch `work` existiert lokal nicht
- Der tatsächliche Arbeitsbranch ist `feat/web-final-trust-folder-flow`

Bewertung:
- Nicht mit dem vorliegenden Repository-Stand deckungsgleich

### Aussage: `git diff --check`

Befund:
- Lokal verifiziert: erfolgreich

Bewertung:
- Korrekt

### Aussage: `pwsh -NoProfile -ExecutionPolicy Bypass -File ./tools/ist_check.ps1` scheitert, weil `pwsh` fehlt

Befund:
- Lokal verifiziert: `pwsh` ist vorhanden
- `tools/ist_check.ps1` läuft erfolgreich durch

Ergebnis des lokalen IST-Checks:
- BOM-Scan: grün
- Mojibake-Scan: grün
- Pflichtdateien vorhanden
- Web-Seiten vorhanden
- Public-QR Pflichttext korrekt vorhanden
- Guard-/Moderator-Checks vorhanden
- Keine dev/actor header Hinweise im Web-API-Client
- Backend-Tests im Projekt-Setup: grün
- `npm ci`: grün
- `npm run build`: grün

Bewertung:
- Die Übergabe ist für dieses System veraltet oder nicht für diese Maschine/Umgebung erstellt worden

### Aussage: `python -m pytest server/tests/test_consent_moderator_block.py -q` scheitert, weil `fastapi` fehlt

Befund:
- Direkt mit System-Python aus `server/` scheitert der Aufruf bereits daran, dass `pytest` in diesem Interpreter nicht installiert ist
- Das Projekt verwendet laut `server/pyproject.toml` Poetry als Standard-Setup
- Im verifizierten Projekt-Setup laufen die Backend-Tests innerhalb von `tools/ist_check.ps1` erfolgreich

Bewertung:
- Die Kernaussage "nacktes Python ohne Projekt-Environment reicht nicht" ist sachlich in diese Richtung korrekt
- Die konkrete Fehlerursache im vorliegenden System ist aber nicht `fastapi fehlt`, sondern `pytest` fehlt im globalen Interpreter

## 3. Tatsächlicher Projektstatus

### Architektur

- Backend: FastAPI unter `server/app`
- Frontend: React + TypeScript + Vite unter `packages/web`
- Source of Truth laut Repo und Doku:
  1. `docs/99_MASTER_CHECKPOINT.md`
  2. `docs/02_PRODUCT_SPEC_UNIFIED.md`
  3. `docs/03_RIGHTS_MATRIX.md`
  4. `docs/01_DECISIONS.md`

### Fachliche und technische Leitplanken

- Security-Modell: deny-by-default + least privilege
- RBAC serverseitig mit object-level checks
- Moderator nur auf `/auth/*`, `/blog/*`, `/news/*`
- Keine PII/Secrets in Logs, Responses oder Exports
- Public-QR Pflichttext ist im Frontend mehrfach korrekt verankert

### Implementierungsstand

Vom erfolgreichen lokalen `ist_check` verifiziert:
- Web-App-Struktur vorhanden (`App.tsx`, Auth, Consent, Vehicles, Documents, Public QR, Trust Folders)
- API-Client vorhanden
- Guards und Moderator-Blockaden im Frontend vorhanden
- Backend-Test-Suite grundsätzlich lauffähig
- Frontend baut erfolgreich produktionsfähig

Zusätzlich ist der aktuelle Branch gegenüber `origin` um genau einen Commit voraus. Der lokale Vorsprung betrifft:
- `docs/02_BACKLOG.md`
- `packages/web/src/authConsentApi.ts`
- `packages/web/src/pages/AuthPage.tsx`
- `packages/web/src/pages/ConsentPage.tsx`
- `packages/web/tests/mini-e2e.spec.ts`

Das deutet auf laufende Arbeiten im Bereich Auth/Consent/Web-E2E hin.

## 4. Bewertung

Das Projekt ist lokal in einem technisch konsistenten und prüfbaren Zustand. Die zentrale Systemprüfung läuft auf dieser Maschine erfolgreich durch. Die gelieferte Übergabe-Beschreibung passt jedoch nicht zum vorliegenden Branch- und Commit-Stand und ist daher nicht als belastbarer IST-Stand dieses Workspaces verwendbar.

Belastbarer IST-Stand für dieses Repo ist stattdessen:
- Branch `feat/web-final-trust-folder-flow`
- HEAD `6bdaf54`
- sauberer Working Tree
- lokaler IST-Check erfolgreich
- Branch lokal noch nicht vollständig mit `origin` synchronisiert (`ahead 1`)

## 5. Empfohlene Arbeitsgrundlage

Für weitere Arbeiten sollte diese Reihenfolge gelten:

1. Tatsächlicher Repo-Zustand (`git status`, `git log`, `tools/ist_check.ps1`)
2. SoT-Dokumente unter `docs/`
3. Projekt-Setup über Poetry und npm statt globalem System-Python

Wenn die erwähnte Übergabe mit Commit `e386b2d` relevant sein soll, muss zuerst geklärt werden, aus welchem Branch oder welcher Repository-Kopie sie stammt.
