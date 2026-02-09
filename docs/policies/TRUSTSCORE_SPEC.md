// File: ./docs/policies/TRUSTSCORE_SPEC.md

# TRUSTSCORE_SPEC – Public-QR Trustscore (Nachweisqualität, nicht Zustand)

**Stand:** 2026-01-28 (Europe/Berlin)  
**Hard Rule:** Public Output ohne Zahlen/Counts/Prozente/Zeiträume

---

## 1) Zweck
Der Trustscore bewertet ausschließlich die **Nachweis-/Dokumentationsqualität** des Servicehefts.
Er bewertet **niemals** den technischen Zustand.

---

## 2) Public Output Contract (MUST)
Public UI/Response darf anzeigen:
- Ampel: Rot / Orange / Gelb / Grün
- Indikatoren (qualitativ, ohne Zahlen):
  - „Historie vorhanden“ (Ja/Nein)
  - „Nachweise vorhanden“ (Ja/Nein)
  - „Verifizierung“ (niedrig/mittel/hoch)
  - „Aktualität/Regelmäßigkeit“ (vorhanden/nicht vorhanden)
  - „Unfallstatus“ (keiner/offen/abgeschlossen)
- Pflicht-Disclaimer (sichtbar, nicht versteckt)

Public UI/Response darf **nicht** anzeigen:
- keine Anzahl Einträge/Dokumente
- keine Prozentwerte
- keine Zeiträume oder relative Zeitangaben (z. B. „vor 6 Monaten“)
- keine Datumsdifferenzen oder „regelmäßig alle X“

---

## 3) Disclaimer (MUST, Public)
„Bewertet die Dokumentationsqualität, nicht den technischen Zustand.“

---

## 4) Inputs (intern, erlaubt)
- Existenz von Historie (Entries)
- Existenz von Nachweisen (Documents) – Quarantäne zählt nicht
- Verifizierungslevel (T1/T2/T3)
- Regelmäßigkeit/Aktualität (intern aus Regeln)
- Unfall-Einträge inkl. Abschluss + Belege

---

## 5) T-Level Definition (kanonisch)
- **T1**: Selbstauskunft (kein belastbarer Fremdbeleg)
- **T2**: Beleg vorhanden (Dokument), nicht akkreditiert verifiziert
- **T3**: akkreditiert verifiziert (Partner/Dealer/Admin Flow), auditpflichtig

---

## 6) Ampel-Entscheidung (intern deterministisch, Public nur qualitativ)
### ROT
- Historie fehlt oder Nachweise fehlen weitgehend.

### ORANGE
- Historie vorhanden, aber lückenhaft; Verifizierung überwiegend niedrig.

### GELB
- Historie + Nachweise solide; Verifizierung gemischt bis mittel; kein offener Unfall ohne Belege.

### GRÜN
- Konsistente Historie + Nachweise; Verifizierung überwiegend hoch.
- Unfalltrust-Regel erfüllt.

---

## 7) Unfalltrust (hard)
- Wenn Unfall vorhanden:
  - GRÜN nur, wenn Unfall „abgeschlossen“ **und** Belege vorhanden.
- Public zeigt nur: „Unfallstatus: offen/abgeschlossen“, keine Details.

---

## 8) Token & Missbrauchsschutz (MUST)
- Public-Token ist rotierbar und revokebar.
- Public endpoints sind read-only und liefern keine PII/CONFIDENTIAL Daten.
- Rate-limits für Public-QR Requests.
