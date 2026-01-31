# docs/04_REPO_STRUCTURE.md
# Repo-Struktur – LifeTimeCircle ServiceHeft 4.0

Diese Datei beschreibt die aktuelle Ordner-/Dateistruktur sowie Regeln für:
- Was gehört ins Repository (Git) / in eine ZIP für Review
- Was bleibt lokal (DB, Uploads, Cache)
- Wo liegt die Source of Truth für Dokumentation

Grundsatz: **produktionsreif, keine Demo**, deny-by-default, least privilege, RBAC **serverseitig enforced**.  
Diese Datei beschreibt **nur Struktur & Nachweisführung** – nicht den technischen Zustand.

---

## 1) Root-Struktur (Überblick)

Empfohlene Struktur im Projekt-Root (Pfadnamen im Repo sind plattformneutral, Windows zeigt ggf. `\`):

```text
LifeTimeCircle-ServiceHeft-4.0/
  docs/
    00_PROJECT_BRIEF.md
    01_DECISIONS.md
    02_BACKLOG.md
    03_RIGHTS_MATRIX.md
    04_REPO_STRUCTURE.md
    05_MODULE_STORY_FORTSETZUNG.md
    99_MASTER_CHECKPOINT.md
    policies/                     (optional; empfohlen sobald Policies wachsen)
    legal/                        (optional/bei Bedarf; Lizenz/Legal Artefakte)
  server/
    app/
      main.py
      settings.py
      rbac.py
      deps.py
      crypto.py
      storage.py
      auth/...
      models/...
      routers/...
    scripts/
    tests/
    data/                         (lokal; DB/Artefakte – nicht in Git/ZIP)
  static/                         (optional; nur versionierte Assets)
  storage/                        (lokal; Uploads/Quarantine – nicht in Git/ZIP)
  tools/                          (Dev-Tools/Helper)
    archive/                      (ARCHIV: nicht SoT, nicht implementieren daraus)
  scripts/                        (Repo-weite Skripte/Checks)
  .env.example
  .gitignore
  README*                         (optional)
  CHANGELOG*                      (optional)
