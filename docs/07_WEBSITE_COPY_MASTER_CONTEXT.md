# LifeTimeCircle – Service Heft 4.0
## Website Copy Master Context (SoT)
Stand: 2026-03-01 (Europe/Berlin)

Kontakt: lifetimecircle@online.de

Einordnung:
- Copy-SoT für Website und Web-App Texte
- fachlich nachgeordnet zu `docs/02_PRODUCT_SPEC_UNIFIED.md`, `docs/03_RIGHTS_MATRIX.md` und `docs/01_DECISIONS.md`
- bei Security-/Rollen-Konflikten gelten immer die technischen SoT-Dokumente

---

# 1) Zweck dieses Dokuments
Dieses Dokument ist die zentrale Copy-Quelle (Website + Web-App Texte) für:
- Frontpage/Hub (öffentlich + Login)
- Service-Heft Kernseiten (eingeloggt)
- Public-QR Mini-Check (öffentlich)
- Blog/News + Newsletter
- Trust-Guide (Ratgeber, „Vertrauen im Autohandel“)

Nicht-Ziele:
- Keine technischen Versprechen, die nicht im MVP/SoT stehen.
- Keine Public-QR-Ausgaben mit Kennzahlen/Counts/Prozenten/Zeiträumen.

---

# 2) Brand-Narrativ (kurz, wiederholbar)
## Kernbotschaft
Proof statt Behauptung.  
LifeTimeCircle macht Fahrzeug-Historie prüfbar: Einträge + Nachweise + klare Rollenlogik.

## Was wir liefern (MVP-Kern)
- Service Heft 4.0: Fahrzeugprofil (VIN/WID), Timeline/Einträge, Dokumente/Nachweise (Uploads)
- Trust-Level je Eintrag/Quelle (T1/T2/T3)
- Public-QR Mini-Check: Ampel Rot/Orange/Gelb/Grün (nur Dokumentations-/Nachweisqualität, ohne Metrics)
- Frontpage/Hub + Login
- Blog/News (Admin erstellt, Moderator nur Blog/News)

---

# 3) Nicht verhandelbare Textregeln (Public / Security / Rollen)
## 3.1 Public-QR Regel (UI & Copy)
Public-QR zeigt keine Kennzahlen/Counts/Prozente/Zeiträume.  
Nur: Ampel + textliche Indikatoren (ohne Halterdaten, ohne Technikzustand).

Pflicht-Disclaimer (exakt, unverändert):
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## 3.2 Rollenwahrheit (keine Marketing-Abkürzungen)
- Public: nur Mini-Check
- User/VIP/Dealer/Admin: Service-Heft Kern
- Moderator: strikt nur Blog/News
- Governance/High-Risk: (Super-)Admin

## 3.3 Sicherheitswahrheit (Copy darf keine Datenleaks triggern)
- Keine Aussagen, die „Public Downloads“ nahelegen.
- Uploads sind Quarantine-by-default; Freigabe nach Scan/Admin.
- Exports: redacted default; Full Export nur Superadmin (high risk).

---

# 4) Tonalität (konkret, ohne Floskeln)
- Kurze Sätze. Aktive Sprache.
- Keine Superlative („bestes“, „revolutionär“).
- Immer: Was ist sichtbar? Was ist nicht sichtbar? (besonders bei Public-QR)
- „Beleg schlägt Behauptung“ als roter Faden.

---

# 5) Navigation / Seitenstruktur (Public + App)
## Public (ohne Login)
1) Start / Hub
2) Public-QR prüfen
3) Blog/News
4) FAQ / Kontakt

## App (mit Login)
1) Fahrzeuge
2) Fahrzeug-Detail (Timeline)
3) Dokumente/Nachweise
4) (Später, VIP/Dealer) Übergabe/Verkauf-QR + Interner Verkauf
5) Admin (Governance)

---

# 6) Seiten-Copy (fertig)

## 6.1 Startseite / Hub (öffentlich)
Header (Navigation)
- Service Heft 4.0
- Public-QR prüfen
- Blog/News
- FAQ
- Kontakt

Hero
Service Heft 4.0 – Nachweise, die man prüfen kann.  
Dokumentiere Service, Wartung, Reparaturen, Umbauten, Prüfungen und Unfall-Infos als Timeline – mit Nachweisen statt Bauchgefühl.

4 Kurz-Argumente
- Timeline statt Zettelchaos: Einträge strukturiert, nachvollziehbar.
- Nachweise statt Aussagen: Dokumente/Belege gehören direkt zum Eintrag.
- Trust-Ampel im Public-Check: sichtbar, aber datenarm – ohne Kennzahlen.
- Rollen & Schutz: Zugriff ist serverseitig geregelt (least privilege).

CTA Buttons
- Einsteigen (führt in Login/Onboarding)
- Public-QR prüfen
- News lesen

Login-Panel
Login per E-Mail.  
Du erhältst einen Verifizierungs-Code oder Magic-Link. Danach bestätigst du AGB & Datenschutz, sonst bleibt der produktive Zugriff gesperrt.

Trust-Hinweis
Wichtig: Public-QR bewertet ausschließlich Dokumentations-/Nachweisqualität. Es ist keine technische Diagnose.

---

## 6.2 Onboarding – Rollenwahl (App)
Titel
Wie nutzt du LifeTimeCircle?

Option A: Privat
Privat / User  
Für dein eigenes Fahrzeug: Timeline, Einträge, Nachweise, Public-QR teilen.

Option B: Gewerblich
Gewerbe / VIP / Dealer  
Zusatzfunktionen für Übergabe/Verkauf und strukturierte Prozesse (nur für Gewerbe, serverseitig gated).

Hinweis
Moderator-Zugriff ist strikt auf Blog/News begrenzt.

---

## 6.3 Service Heft 4.0 (Produktseite, öffentlich)
Titel
Was ist das Service Heft 4.0?

Copy
Das Service Heft 4.0 ist deine dokumentierte Fahrzeug-Historie:
- Fahrzeugprofil über VIN/WID
- Timeline mit Einträgen (z. B. Wartung, Reparatur, Umbau, Prüfung, Unfall)
- Nachweise als Uploads, die zum Eintrag gehören
- Trust-Level pro Eintrag/Quelle (T1/T2/T3)

Verifizierungslevel (T1/T2/T3)
- T1: physisches Serviceheft nicht vorhanden
- T2: physisches Serviceheft vorhanden
- T3: Dokument vorhanden

Unfalltrust (kurz)
Wenn ein Unfall relevant ist, zählt nicht „unfallfrei“ als Wort, sondern Abschluss + Belege für grüne Einstufung.

---

## 6.4 Fahrzeuge – Empty State (App)
Titel
Noch kein Fahrzeug angelegt.

Copy
Lege dein Fahrzeug über VIN/WID an. Danach kannst du Einträge und Nachweise hinzufügen.  
Hinweis: Public und Moderator können keine Fahrzeuge anlegen.

Button
Fahrzeug anlegen

---

## 6.5 Fahrzeug-Detail – Timeline (App)
Titel
Timeline

Kurztext
Jeder Eintrag hat Pflichtfelder (Datum, Typ, durchgeführt von, Kilometerstand).  
Optionalfelder verbessern die Trust-Stufe und die Nachweisqualität.

„Durchgeführt von“ (Taxonomie)
- Fachwerkstatt
- Händler
- Autohaus
- Reifenservice
- Tuning-Fachbetrieb
- Gesetzliches (TÜV/Gutachten/Wertgutachten)
- Eigenleistung
- Sonstiges

CTA
- Eintrag hinzufügen
- Nachweis hochladen

---

## 6.6 Dokumente/Nachweise (App)
Titel
Nachweise

Copy (klar, ohne Security-Details zu leaken)
Uploads werden standardmäßig geprüft und erst nach Freigabe wie vorgesehen nutzbar.  
Im Public-QR werden keine Dokumente, keine Downloads und keine Metadaten gezeigt.

Upload-Hinweis (UI)
Bitte lade nur passende Nachweise hoch (z. B. Rechnung, Prüfbericht, Foto zur Arbeit). Keine sensiblen Daten in Freitext.

---

## 6.7 Public-QR Mini-Check (öffentlich)
Titel
Public-QR Mini-Check

Copy
Die Trust-Ampel zeigt, wie gut die Historie dokumentiert und nachweisbar ist – nicht, wie „gut“ das Fahrzeug technisch ist.

Was du siehst
- Ampel: Rot / Orange / Gelb / Grün
- Textliche Indikatoren (ohne Zahlen)

Was du nicht siehst
- Keine Kennzahlen/Counts/Prozente/Zeiträume
- Keine Halterdaten
- Keine Dokumente/Downloads
- Keine technischen Diagnosen

Pflicht-Disclaimer (exakt)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## 6.8 Blog/News (öffentlich)
Titel
News & Updates

Intro
Hier stehen Produkt-Updates, Hinweise zur Dokumentation und praxisnahe Checklisten.  
Moderator kann Inhalte vorbereiten; Veröffentlichung erfolgt final wie vorgesehen.

Newsletter (Opt-in Text)
Wenn du Updates per E-Mail willst: Newsletter abonnieren. Du kannst jederzeit abmelden.

---

## 6.9 FAQ (öffentlich)
Q: Bewertet die Trust-Ampel den technischen Zustand?
Nein. Sie bewertet ausschließlich Dokumentations- und Nachweisqualität.  
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

Q: Warum zeigt Public-QR keine Zahlen?
Weil Public bewusst datenarm ist. Du bekommst Indikatoren, aber keine Kennzahlen.

Q: Was brauche ich für „Grün“?
Grün bedeutet: Historie ist vorhanden, Verifizierungsgrad ist hoch, Aktualität ist plausibel – und bei Unfall gilt: Grün nur bei Abschluss + Belegen.

Q: Kann ich Dokumente öffentlich teilen?
Nein. Public zeigt keine Dokumente, keine Downloads und keine Metadaten.

Q: Kontakt?
lifetimecircle@online.de

---

# 7) Trust-Guide (Ratgeber): Arbeitsqualität „Vertrauen im Autohandel“
Dieser Teil ist als Blog-Artikelserie oder als VIP-PDF geeignet. Er ist bewusst generisch und belege-orientiert.

## 7.1 Kurzprinzip
Vertrauen entsteht durch Belege.  
Worte/Story zählen nur, wenn sie durch Dokumentation und Prozesse gedeckt sind.

## 7.2 Öffentliche Indikatoren (was man als Käufer sieht)
1) Transparenz im Angebot: klare Angaben zu Zustand, Historie, Schäden/Unfallstatus.
2) Prozesssichtbarkeit: Aufbereitung, Übergabe, Checklisten, wiederholbare Standards.
3) Unternehmenssignale: Impressum, Erreichbarkeit, konsistente Firmendaten, nachvollziehbare Bewertungen.
4) Vertrag & Recht: klare Gewährleistung, keine verwirrenden Konstrukte, verständliche Dokumente.
5) After-Sales: Erreichbarkeit, Reklamationskultur, saubere Kulanzlogik.

## 7.3 Trust-Checks (Checkliste, 10 Punkte)
1) Service-/Rechnungs-Historie vollständig?
2) HU/AU, Gutachten, Prüfberichte vorhanden?
3) Unfallstatus klar (nicht „unbekannt“ wegwischen)?
4) Lack-/Zustandsprotokoll vorhanden (oder unabhängiger Check)?
5) Diagnose-/Fehlerbericht vorhanden (wenn relevant)?
6) Übergabeprotokoll inkl. Mängel & Zusagen?
7) Vertrag: Zustand, KM-Stand, Zusicherungen klar formuliert?
8) Kosten: Überführung/Nebenleistungen transparent?
9) Kommunikation: klare Antworten ohne Druck?
10) Nach dem Kauf erreichbar (schriftliche Kanäle)?

## 7.4 Scorecard (0–5 je Feld)
- Transparenz
- Dokumentationsqualität
- Prozessstandard
- Vertrag & Rechtssicherheit
- Kommunikation
- After-Sales
- Preis-/Angebotsintegrität
- Reputation & Konsistenz

Interpretation:
- 20–25: sehr hoch
- 14–19: solide, gezielt prüfen
- <14: erhöhtes Risiko

---

# 8) Copy-Snippets (Microcopy Library)
Buttons
- Einsteigen
- Public-QR prüfen
- Fahrzeug anlegen
- Eintrag hinzufügen
- Nachweis hochladen
- News lesen
- Newsletter abonnieren

Systemhinweise (kurz)
- Datenpflege = bessere Trust-Stufe & Verkaufswert.
- Public zeigt keine Kennzahlen und keine Dokumente.
- Ohne bestätigte AGB/Datenschutz kein produktiver Zugriff.

Error/Empty States (neutral)
- Zugriff nicht erlaubt.
- Anmeldung erforderlich.
- Zustimmung erforderlich, bitte AGB/Datenschutz bestätigen.
- Nicht gefunden.

---

# 9) Meta-Texte (SEO / Share)
Startseite
Title: „LifeTimeCircle – Service Heft 4.0 | Nachweise statt Behauptung“
Description: „Dokumentiere Fahrzeug-Historie als Timeline mit Nachweisen. Public-QR zeigt Trust als Ampel – ohne Kennzahlen und ohne Technikbewertung.“

Public-QR
Title: „LifeTimeCircle Public-QR | Trust-Ampel (Dokumentationsqualität)“
Description: „Datenarmer Mini-Check: Ampel Rot/Orange/Gelb/Grün. Keine Kennzahlen, keine Dokumente, keine Technikdiagnose.“

ENDE
