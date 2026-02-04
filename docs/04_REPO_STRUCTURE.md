# Repo-Struktur – LifeTimeCircle ServiceHeft 4.0



Diese Datei beschreibt die aktuelle Ordner-/Dateistruktur sowie Regeln für:

- Was gehört ins Repository (Git) / in eine ZIP für Review

- Was bleibt lokal (DB, Uploads, Cache)

- Wo liegt die Source of Truth für Dokumentation



Grundsatz: **produktionsreif, keine Demo**, default deny, serverseitig enforced RBAC.  

Diese Datei beschreibt **nur Struktur & Nachweisführung** – nicht den technischen Zustand.



---



## 1) Root-Struktur (Überblick)



Empfohlene Struktur im Projekt-Root:



LifeTimeCircle-ServiceHeft-4.0

docs

00_PROJECT_BRIEF.md

01_DECISIONS.md

02_BACKLOG.md

03_RIGHTS_MATRIX.md

04_REPO_STRUCTURE.md

05_MODULE_STORY_FORTSETZUNG.md

99_MASTER_CHECKPOINT.md

policies\ (optional, empfohlen sobald Policies wachsen)

server

app

main.py

settings.py

rbac.py

deps.py

crypto.py

storage.py

auth...

models...

routers...

scripts

tests

data\ (lokal; DB/Artefakte – nicht in Git/ZIP)

static

storage\ (lokal; Uploads/Quarantine – nicht in Git/ZIP)

tools

scripts

.env.example

README*

CHANGELOG*

.gitignore





---



## 2) Source of Truth (Doku)



**Source of Truth** für Projekt-Entscheidungen, Rechte und Checkpoints ist:

- `docs\`



Wichtige Dateien:

- `00_PROJECT_BRIEF.md` – Leitplanken / Zielbild / Grundprinzipien

- `01_DECISIONS.md` – verbindliche Entscheidungen (nicht „vielleicht“)

- `02_BACKLOG.md` – Tasks/Features, Priorität/Status

- `03_RIGHTS_MATRIX.md` – Rollen & Rechte (serverseitig enforced)

- `99_MASTER_CHECKPOINT.md` – aktueller Stand + Next Focus + DoD

- `04_REPO_STRUCTURE.md` – diese Datei (Struktur & Regeln)

- `05_MODULE_STORY_FORTSETZUNG.md` – Modulgeschichte / Kontext



Optional:

- `docs\policies\` – wächst mit, wenn es mehr Security/Privacy/Export/Upload Policies gibt



---



## 3) Server (Backend) – Struktur & Verantwortlichkeiten



Pfad:

- `server\`



### 3.1 `server\app\` (Runtime-Code)

Typische Kernbereiche:



- `main.py`

  - FastAPI App, Router-Registrierung, Startup/Shutdown

  - Keine Business-Logik „verstecken“, nur Verdrahtung



- `settings.py`

  - Konfiguration via Env

  - Keine Secrets hardcoden

  - DEV-Flags klar getrennt von PROD



- `rbac.py`

  - Rollen, Berechtigungsprüfungen

  - Default deny: wenn unklar → Zugriff verweigern

  - RBAC wird serverseitig erzwungen (kein „nur Frontend“)



- `deps.py`

  - Dependencies (z.B. DB session, current user)

  - Keine Klartext-PII in Logs



- `crypto.py`

  - HMAC/Pseudonymisierung, Verschlüsselungsfunktionen

  - Kein unsalted SHA für Pseudonyme (HMAC verwenden)

  - Schlüssel nie loggen



- `storage.py`

  - Upload/Download/Quarantine-Logik

  - Allowlist + Limits + Quarantine by default

  - Keine öffentlichen Uploads



Unterordner (typisch):

- `auth\` – Login, Challenge/OTP, Sessions

- `models\` – DB-Modelle

- `routers\` – API-Endpunkte nach Bereichen



### 3.2 `server\tests\`

- Automatisierte Tests (RBAC, Auth-Flows, Exports, Logs/Audit)

- Ziel: produktionsreife Regression-Sicherheit



### 3.3 `server\scripts\`

- Helfer-Skripte (PowerShell/Python) für Patch, Run, Audit Tail etc.

- Diese Skripte gehören ins Repo, weil sie reproduzierbar sein müssen



### 3.4 `server\data\` (lokal)

- Lokale Datenbank / lokale Artefakte

- **Nicht** in Git und **nicht** in ZIP (Review)

- Beispiel: `server\data\app.db`



---



## 4) Storage/Uploads (lokal)



Pfad:

- `storage\`



Regeln:

- Uploads: Allowlist + Limits + Quarantine by default

- Quarantine-Freigabe nur nach Scan oder Admin-Approval (gemäß Policy)

- **Kein** öffentliches Serving von Uploads

- Ordner bleibt **lokal** (nicht in Git/ZIP), außer ihr legt explizit eine leere Struktur an:

  - dann nur `.gitkeep` Dateien, keine Inhalte



---



## 5) Static / Tools / Scripts (Repo-weit)



- `static\`

  - Frontend assets oder statische Ressourcen (wenn genutzt)

  - Nur das, was wirklich versioniert werden soll



- `tools\`

  - Dev-Tools/Helper (z.B. Generatoren, Migrationshelfer)



- `scripts\` (Root)

  - Repo-weite Skripte wie `quick_check.ps1`

  - Standardisierte Checks/DoD-Checks vor ZIP/Commit



---



## 6) Regeln für Git und ZIP (Review-Paket)



### 6.1 In Git / ZIP **enthalten**

- `docs\**` (komplett)

- `server\app\**`

- `server\tests\**`

- `server\scripts\**`

- Root-`scripts\**`

- `tools\**` (wenn relevant)

- `static\**` (wenn relevant)

- `.env.example`, `.gitignore`, README/CHANGELOG (wenn vorhanden)



### 6.2 **Nicht** in Git / ZIP enthalten (lokal)

- `server\data\app.db` (und generell `server\data\*` Inhalte)

- `storage\*` Inhalte (Uploads/Quarantine)

- `__pycache__`, `.pytest_cache`, `.venv`, `node_modules`, Build-Outputs

- Logfiles, Dumps, temporäre Dateien



### 6.3 Datenschutz / Logs / Exports (Strukturregeln)

- Keine Secrets in Logs

- Keine Klartext-PII in Logs/Exports

- Pseudonymisierung: HMAC (kein unsalted SHA)

- Exports standardmäßig redacted

- Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung



---



## 7) Konventionen (kurz & praktisch)



### 7.1 Dateinamen

- Docs: `NN_NAME.md` (z.B. 04_REPO_STRUCTURE.md)

- Scripts: sprechende Namen, keine kryptischen Kürzel



### 7.2 „Ein Ort pro Wahrheit“

- Struktur-Regeln → `04_REPO_STRUCTURE.md`

- Rechte/RBAC → `03_RIGHTS_MATRIX.md`

- Status/Next Focus/DoD → `99_MASTER_CHECKPOINT.md`

- Entscheidungen → `01_DECISIONS.md`



### 7.3 Default deny

Wenn bei einer Route / Funktion unklar ist, wer Zugriff haben soll:

- Zugriff **verweigern** und Entscheidung in `01_DECISIONS.md` dokumentieren.



---



## 8) Schnelle Befehle (lokale Kontrolle)



### 8.1 Root prüfen

```powershell

cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

dir
