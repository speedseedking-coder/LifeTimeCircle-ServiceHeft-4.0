# LifeTimeCircle – Quick-Reference Checklist
## Laufende Finalisierung ab 2026-03-01

Diese Datei ist die operative Tagescheckliste für den aktuellen Projektstand.
Sie ersetzt keine SoT-Dokumente und keine Git-Historie.

---

## 1) Vor jeder Änderung

- [ ] `docs/00_CODEX_CONTEXT.md` geprüft
- [ ] `docs/03_RIGHTS_MATRIX.md` geprüft
- [ ] `docs/99_MASTER_CHECKPOINT.md` geprüft
- [ ] relevante Produktlogik in `docs/02_PRODUCT_SPEC_UNIFIED.md` geprüft
- [ ] bei UI-/Textänderungen `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md` geprüft

---

## 2) Harte Invarianten

- [ ] deny-by-default bleibt unangetastet
- [ ] RBAC bleibt serverseitig führend
- [ ] Moderator bleibt außerhalb von Blog/News gesperrt
- [ ] keine PII in Logs, Exports oder Public-Views
- [ ] Uploads bleiben Quarantäne-by-default
- [ ] Public-QR-Disclaimer bleibt exakt

Pflichttext:
> Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.

---

## 3) Tagesstart

- [ ] Working Tree verstanden
- [ ] offenes Paket klar benannt
- [ ] betroffene Dateien identifiziert
- [ ] keine SoT-Widersprüche offen

Wenn unklar:
- zuerst `99_MASTER_CHECKPOINT.md`
- dann `00_CODEX_CONTEXT.md`
- dann `03_RIGHTS_MATRIX.md`

---

## 4) Während der Arbeit

- [ ] bestehende Patterns wiederverwenden
- [ ] keine unnötigen Parallelpfade in Docs erzeugen
- [ ] lokale Änderungen klein und verifizierbar halten
- [ ] nach größeren UI-Paketen Build und E2E ausführen

---

## 5) Nach jedem Paket

- [ ] `git diff --check`
- [ ] passender Build/Test-Lauf grün
- [ ] bei größeren Paketen `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\test_all.ps1`
- [ ] bei repo-relevantem Stand `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ist_check.ps1`
- [ ] Doku nur dann aktualisieren, wenn sich der reale Stand geändert hat

---

## 6) Aktueller verifizierter Fokus

Stand 2026-03-01:

- [x] Repo-Gates stabilisiert
- [x] Kernseiten A11y gehärtet
- [x] Mobile 375px gehärtet
- [x] Desktop 1920px gehärtet
- [x] `99_MASTER_CHECKPOINT.md` entschlackt
- [x] `07_WEBSITE_COPY_MASTER_CONTEXT.md` eingeordnet
- [x] `11_MASTERPLAN_INDEX.md` und `11_MASTERPLAN_READING_ORDER.md` auf Live-Stand gezogen
- [ ] übrige Masterplan-Dokumente dauerhaft konsistent halten
- [ ] verbleibende Produkt- und Release-Restarbeiten gezielt bündeln

---

## 7) Empfohlene Tagesreihenfolge

1. Status prüfen
2. Paket benennen
3. Kontext lesen
4. Änderung umsetzen
5. Build/Test ausführen
6. Doku nur bei echtem Statusgewinn nachziehen
7. clean commit

---

## 8) Stop-Kriterien

Nicht einfach weitermachen, wenn:

- Rollenlogik unklar ist
- der Public-QR-Text betroffen ist
- Tests kippen und Ursache unklar ist
- eine Änderung den SoT-Dokumenten widerspricht

Dann zuerst:
- Ursache lokalisieren
- SoT prüfen
- nur mit belastbarer Richtung weiterarbeiten

---

## 9) Definition von "heute grün"

Der Tag gilt nur dann als sauber abgeschlossen, wenn:

- die Änderungen verständlich abgegrenzt sind
- der passende Testlauf grün ist
- der Working Tree bewusst sauber oder bewusst offen ist
- die Doku nicht mehr behauptet als der Code wirklich liefert

---

## 10) Kurzfassung

Arbeite nicht gegen den verifizierten Stand.
Arbeite vom verifizierten Stand aus.
