# LifeTimeCircle – Service Heft 4.0
## Masterplan zur Finalisierung
**Stand: 2026-03-01 (Europe/Berlin)**

---

## Executive Summary

Das Projekt ist nicht mehr in einer hypothetischen Startphase.
Der Kern des Produkts ist im Repo bereits vorhanden und lokal verifizierbar.

Aktueller Gesamtzustand:
- Backend ist testbar und produktionsnah.
- Web-Core-Flows sind real angebunden.
- Accessibility- und Responsive-Hardening ist auf Kernseiten weit fortgeschritten.
- Repo-Gates sind lokal grün.
- Der größte verbleibende Aufwand liegt in Produktreife, Doku-Konsistenz und gezieltem Rest-Polish.

Verbindlicher Ist-Stand:
- `docs/99_MASTER_CHECKPOINT.md`

---

## Zielbild

Ziel bleibt ein produktives MVP, kein Demo-Stand.

Dafür müssen folgende Eigenschaften gleichzeitig erfüllt sein:
- funktionierende Kernflows von Auth bis Admin
- serverseitig durchgesetzte Rollen- und Sicherheitsregeln
- belastbare Web-Qualität auf Mobile und Desktop
- nachvollziehbare SoT-Dokumentation
- grüne lokale Verifikations-Gates

---

## Realer Arbeitsstand am 2026-03-01

### Bereits belastbar vorhanden
- Auth- und Consent-Gating
- Vehicles und Vehicle Detail
- Documents inkl. Upload-/Lookup-/Quarantänefluss
- Public-QR mit Pflicht-Disclaimer
- Admin-Rollen, VIP-Businesses und Export-Step-up
- Blog/News
- Playwright-Mini-E2E über Kernpfade

### Kürzlich stabilisiert
- Repo-Gates und Build/Test-Basis
- Content- und Formular-A11y
- Mobile-Hardening auf 375px
- Desktop-/1920px-Finetuning für Core-Workspaces
- SoT-Dokumente `99_MASTER_CHECKPOINT`, `MASTERPLAN_INDEX`, `READING_ORDER`

### Noch offen
- übrige Masterplan-Dokumente auf Live-Stand halten
- Rest-Polish auf Spezialfällen und Randkomponenten
- Release-/Deployment-Entscheidungen sauber dokumentieren

---

## Strategische Finalisierungsachsen

### 1. Workspace-Stabilität
Zuerst bleibt der verifizierbare Zustand wichtig.

Definition:
- `tools/test_all.ps1` grün
- `tools/ist_check.ps1` grün
- Working Tree clean

### 2. Produktreife der Kernflows
Nicht neue Seitenspuren priorisieren, sondern die vorhandenen Kernpfade weiter absichern:
- Vehicles
- Vehicle Detail
- Documents
- Public-QR
- Admin

### 3. SoT-Konsistenz
Planungsdokumente dürfen nicht mehr so tun, als stünde der Projektstart noch bevor.
Plan und Ist-Zustand müssen getrennt lesbar sein.

### 4. Release-Vorbereitung
Sobald Doku und Kernflows stabil sind:
- Rest-Risiken bündeln
- Deployment-/Betriebsfragen dokumentieren
- Go-/No-Go-Kriterien explizit machen

---

## Priorisierte nächste Pakete

Stand heute:

1. Masterplan-Dokumente von alten Kalender- und Sprintannahmen entkoppeln.
2. Verbleibende UI-/A11y-Randfälle gezielt härten.
3. Release-nahe Checks und Betriebsdokumentation vorbereiten.

Nicht priorisiert:
- neue große Feature-Blöcke ohne klaren Bezug zum verifizierten Kern
- doppelte Dokumentationspfade
- historische PR-Chroniken in SoT-Dokumenten

---

## Entscheidungsprinzipien

Bei jeder weiteren Finalisierung gilt:
- SoT vor Planungsnotiz
- grüner Workspace vor neuem Scope
- Security- und Rollenwahrheit vor UX-Abkürzung
- verifizierte Umsetzung vor theoretischer Roadmap

---

## Realistische Release-Definition

Release-ready bedeutet hier nicht nur "Feature sichtbar", sondern:

- Backend-Tests grün
- Web-Build grün
- Playwright-Kernpfade grün
- keine offenen SoT-Widersprüche in Kern-Dokumenten
- Public-QR-Disclaimer korrekt
- RBAC/deny-by-default unverletzt
- Mobile und Desktop auf Kernseiten belastbar

---

## Arbeitsmodus für die nächsten Schritte

Empfohlenes Vorgehen:

1. vor jeder Änderung `99_MASTER_CHECKPOINT.md` prüfen
2. relevante Rollen-/Pfadregeln in `03_RIGHTS_MATRIX.md` prüfen
3. Änderung umsetzen
4. mindestens Web-Build und passende Tests ausführen
5. bei größeren Paketen `tools/test_all.ps1` und `tools/ist_check.ps1` nachziehen

---

## Schlussfolgerung

Die Finalisierung ist jetzt kein klassischer Sprint-Start mehr, sondern kontrollierte Restarbeit auf einem bereits funktionierenden Kern.

Der richtige Fokus für März 2026 ist:
- Stabilität halten
- Lücken schließen
- Dokumentation ehrlich halten
- nur noch zielgerichtete Produktarbeit auf dem verifizierten Stand durchführen
