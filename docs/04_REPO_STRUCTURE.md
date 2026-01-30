\# Repo-Struktur – LifeTimeCircle ServiceHeft 4.0



Diese Datei beschreibt die aktuelle Ordner-/Dateistruktur sowie Regeln für:

\- Was gehört ins Repository (Git) / in eine ZIP für Review

\- Was bleibt lokal (DB, Uploads, Cache)

\- Wo liegt die Source of Truth für Dokumentation



Grundsatz: \*\*produktionsreif, keine Demo\*\*, default deny, serverseitig enforced RBAC.  

Diese Datei beschreibt \*\*nur Struktur \& Nachweisführung\*\* – nicht den technischen Zustand.



---



\## 1) Root-Struktur (Überblick)



Empfohlene Struktur im Projekt-Root:



LifeTimeCircle-ServiceHeft-4.0

docs

00\_PROJECT\_BRIEF.md

01\_DECISIONS.md

02\_BACKLOG.md

03\_RIGHTS\_MATRIX.md

04\_REPO\_STRUCTURE.md

05\_MODULE\_STORY\_FORTSETZUNG.md

99\_MASTER\_CHECKPOINT.md

policies\\ (optional, empfohlen sobald Policies wachsen)

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

data\\ (lokal; DB/Artefakte – nicht in Git/ZIP)

static

storage\\ (lokal; Uploads/Quarantine – nicht in Git/ZIP)

tools

scripts

.env.example

README\*

CHANGELOG\*

.gitignore





---



\## 2) Source of Truth (Doku)



\*\*Source of Truth\*\* für Projekt-Entscheidungen, Rechte und Checkpoints ist:

\- `docs\\`



Wichtige Dateien:

\- `00\_PROJECT\_BRIEF.md` – Leitplanken / Zielbild / Grundprinzipien

\- `01\_DECISIONS.md` – verbindliche Entscheidungen (nicht „vielleicht“)

\- `02\_BACKLOG.md` – Tasks/Features, Priorität/Status

\- `03\_RIGHTS\_MATRIX.md` – Rollen \& Rechte (serverseitig enforced)

\- `99\_MASTER\_CHECKPOINT.md` – aktueller Stand + Next Focus + DoD

\- `04\_REPO\_STRUCTURE.md` – diese Datei (Struktur \& Regeln)

\- `05\_MODULE\_STORY\_FORTSETZUNG.md` – Modulgeschichte / Kontext



Optional:

\- `docs\\policies\\` – wächst mit, wenn es mehr Security/Privacy/Export/Upload Policies gibt



---



\## 3) Server (Backend) – Struktur \& Verantwortlichkeiten



Pfad:

\- `server\\`



\### 3.1 `server\\app\\` (Runtime-Code)

Typische Kernbereiche:



\- `main.py`

&nbsp; - FastAPI App, Router-Registrierung, Startup/Shutdown

&nbsp; - Keine Business-Logik „verstecken“, nur Verdrahtung



\- `settings.py`

&nbsp; - Konfiguration via Env

&nbsp; - Keine Secrets hardcoden

&nbsp; - DEV-Flags klar getrennt von PROD



\- `rbac.py`

&nbsp; - Rollen, Berechtigungsprüfungen

&nbsp; - Default deny: wenn unklar → Zugriff verweigern

&nbsp; - RBAC wird serverseitig erzwungen (kein „nur Frontend“)



\- `deps.py`

&nbsp; - Dependencies (z.B. DB session, current user)

&nbsp; - Keine Klartext-PII in Logs



\- `crypto.py`

&nbsp; - HMAC/Pseudonymisierung, Verschlüsselungsfunktionen

&nbsp; - Kein unsalted SHA für Pseudonyme (HMAC verwenden)

&nbsp; - Schlüssel nie loggen



\- `storage.py`

&nbsp; - Upload/Download/Quarantine-Logik

&nbsp; - Allowlist + Limits + Quarantine by default

&nbsp; - Keine öffentlichen Uploads



Unterordner (typisch):

\- `auth\\` – Login, Challenge/OTP, Sessions

\- `models\\` – DB-Modelle

\- `routers\\` – API-Endpunkte nach Bereichen



\### 3.2 `server\\tests\\`

\- Automatisierte Tests (RBAC, Auth-Flows, Exports, Logs/Audit)

\- Ziel: produktionsreife Regression-Sicherheit



\### 3.3 `server\\scripts\\`

\- Helfer-Skripte (PowerShell/Python) für Patch, Run, Audit Tail etc.

\- Diese Skripte gehören ins Repo, weil sie reproduzierbar sein müssen



\### 3.4 `server\\data\\` (lokal)

\- Lokale Datenbank / lokale Artefakte

\- \*\*Nicht\*\* in Git und \*\*nicht\*\* in ZIP (Review)

\- Beispiel: `server\\data\\app.db`



---



\## 4) Storage/Uploads (lokal)



Pfad:

\- `storage\\`



Regeln:

\- Uploads: Allowlist + Limits + Quarantine by default

\- Quarantine-Freigabe nur nach Scan oder Admin-Approval (gemäß Policy)

\- \*\*Kein\*\* öffentliches Serving von Uploads

\- Ordner bleibt \*\*lokal\*\* (nicht in Git/ZIP), außer ihr legt explizit eine leere Struktur an:

&nbsp; - dann nur `.gitkeep` Dateien, keine Inhalte



---



\## 5) Static / Tools / Scripts (Repo-weit)



\- `static\\`

&nbsp; - Frontend assets oder statische Ressourcen (wenn genutzt)

&nbsp; - Nur das, was wirklich versioniert werden soll



\- `tools\\`

&nbsp; - Dev-Tools/Helper (z.B. Generatoren, Migrationshelfer)



\- `scripts\\` (Root)

&nbsp; - Repo-weite Skripte wie `quick\_check.ps1`

&nbsp; - Standardisierte Checks/DoD-Checks vor ZIP/Commit



---



\## 6) Regeln für Git und ZIP (Review-Paket)



\### 6.1 In Git / ZIP \*\*enthalten\*\*

\- `docs\\\*\*` (komplett)

\- `server\\app\\\*\*`

\- `server\\tests\\\*\*`

\- `server\\scripts\\\*\*`

\- Root-`scripts\\\*\*`

\- `tools\\\*\*` (wenn relevant)

\- `static\\\*\*` (wenn relevant)

\- `.env.example`, `.gitignore`, README/CHANGELOG (wenn vorhanden)



\### 6.2 \*\*Nicht\*\* in Git / ZIP enthalten (lokal)

\- `server\\data\\app.db` (und generell `server\\data\\\*` Inhalte)

\- `storage\\\*` Inhalte (Uploads/Quarantine)

\- `\_\_pycache\_\_`, `.pytest\_cache`, `.venv`, `node\_modules`, Build-Outputs

\- Logfiles, Dumps, temporäre Dateien



\### 6.3 Datenschutz / Logs / Exports (Strukturregeln)

\- Keine Secrets in Logs

\- Keine Klartext-PII in Logs/Exports

\- Pseudonymisierung: HMAC (kein unsalted SHA)

\- Exports standardmäßig redacted

\- Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung



---



\## 7) Konventionen (kurz \& praktisch)



\### 7.1 Dateinamen

\- Docs: `NN\_NAME.md` (z.B. 04\_REPO\_STRUCTURE.md)

\- Scripts: sprechende Namen, keine kryptischen Kürzel



\### 7.2 „Ein Ort pro Wahrheit“

\- Struktur-Regeln → `04\_REPO\_STRUCTURE.md`

\- Rechte/RBAC → `03\_RIGHTS\_MATRIX.md`

\- Status/Next Focus/DoD → `99\_MASTER\_CHECKPOINT.md`

\- Entscheidungen → `01\_DECISIONS.md`



\### 7.3 Default deny

Wenn bei einer Route / Funktion unklar ist, wer Zugriff haben soll:

\- Zugriff \*\*verweigern\*\* und Entscheidung in `01\_DECISIONS.md` dokumentieren.



---



\## 8) Schnelle Befehle (lokale Kontrolle)



\### 8.1 Root prüfen

```powershell

cd "C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0"

dir



