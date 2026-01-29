# LifeTimeCircle – Service Heft 4.0
**Project Brief (Single Source of Truth)**  
Stand: 2026-01-27 (Europe/Berlin)

## 1) Kurzbeschreibung
**LifeTimeCircle** ist die Plattform (digitale Fahrzeugwelt).  
**Service Heft 4.0** ist das Kernprodukt: ein digitales, verifizierbares Lebenslauf-/Serviceheft für Fahrzeuge – mit Dokumentation, Nachweisen, Verifizierungsstufen und (optional) Public-QR Mini-Check.

**Oberste Prämisse:** Kein Demo-Charakter. Es soll **produktionsreif** gedacht und umgesetzt werden.

Kontakt: **lifetimecircle@online.de**

## 2) Ziele
- **Fahrzeug-Historie & Vertrauen**: Nachvollziehbare Einträge + Nachweise (Dokumente/Bilder), auch für Reimporte, Restaurierungen, Unfallinstandsetzungen.
- **Standardisierung**: Service- und Ereignis-Historie wird zentral, verifizierbar, exportierbar.
- **Transparenz nach außen**: Public-QR Mini-Check zeigt **Dokumentationsqualität** (nicht technischen Zustand).

## 3) Nicht-Ziele (bewusst NICHT)
- **Keine** Aussage zum **technischen Zustand** per Public-QR.
- **Keine** frei zugängliche Halterdaten-Auskunft.
- Fahrzeugverkauf/Übergabe-QR und „interner Verkauf“ **nicht** für normale User (nur VIP/Händler).

## 4) Rollen & Rechte (high-level)
Rollen (Basis):
- **public**: Zugriff nur über Public-QR Mini-Check (sehr eingeschränkte Ansicht)
- **user**: eigenes Konto, eigene Fahrzeuge, eigene Einträge
- **vip**: erweiterte Features (z. B. tiefere Dokument-/Bildansicht; ggf. Übergabe/Verkauf)
- **dealer (gewerblich)**: Händlerfunktionalität (VIP-nah), ggf. Multi-User, Übergabe/Verkauf
- **moderator**: nur News/Blog-Bereich, stark eingeschränkt (keine/kaum Halterdaten)
- **admin (Oberadmin)**: volle Rechte, Freischaltungen, Regeln, Moderatoren akkreditieren

Sonderregel:
- **VIP-Gewerbe**: bis zu **2 Mitarbeiterplätze**, aber **nur nach Admin-Prüfung/Freigabe**.

## 5) Zugang / Anmeldung
- **E-Mail-Login** mit **Verifizierung** (Code oder Magic-Link).
- Registrierung/Anmeldung nur gültig, wenn **AGB** und **Datenschutz** bestätigt wurden.

## 6) Kernmodule (MVP)
### 6.1 Service Heft 4.0 (Kern)
- Fahrzeugprofil (Fahrzeug-ID / VIN/WID / Basisdaten)
- Ereignisse/Einträge (Timeline):
  - Wartung/Service
  - Reparatur
  - Umbau/Restauration
  - Unfall & Instandsetzung
  - Dokumente/Nachweise (Rechnungen, Prüfberichte etc.)
- Verifizierungsstufen (T1/T2/T3) je Eintrag/Quelle *(Definition: siehe Backlog – noch zu finalisieren)*

### 6.2 Public-QR Mini-Check (Trust-Ampel)
- Ampelsystem: **Rot / Orange / Gelb / Grün**
- Bewertet **nur Dokumentations-/Nachweisqualität**, **nicht** den technischen Zustand.
- Kriterien (mindestens):
  - Historie vorhanden
  - Verifizierungsgrad (T3/T2/T1)
  - Aktualität/Regelmäßigkeit
  - Unfalltrust: **Grün** bei Unfall nur bei **Abschluss + Belegen**
- Pflicht-Disclaimer (Public): „Bewertet die Dokumentationsqualität, nicht den Zustand.“

### 6.3 Hub / Frontpage
- Startseite mit Erklärtext
- Obere Headerbar mit Modulen/Tools
- Login-Bereich links oder rechts (Standard: **links**, falls nicht anders festgelegt)
- „Zutrittsknopf“ / Call-to-action

### 6.4 Blogbase + Newsletter (Admin)
- Blogbase: News/Beiträge vom Oberadmin
- Newsletter: Versand an Userschaft + Rückkanal (Kontakt/Feedback)

## 7) Datenschutz & Sicherheit (Leitlinien)
- Datenminimierung: Public zeigt nur „Trust“, keine Halterdaten.
- Rollenbasierte Rechte: VIP/Händler erweitern, Moderator stark begrenzen.
- Verifizierung nachvollziehbar protokollieren (wer/was/wann).

## 8) MVP-Sprints (Vorschlag)
### Sprint A – Fundament
- Projektbranding + Struktur
- Login + Verifizierung + AGB/Datenschutz Pflicht
- Rollen & Rechte (Basis)
- Minimal-Admin: User/Rollen/Einladungen

### Sprint B – Service Heft Kern
- Fahrzeug anlegen/suchen
- Fahrzeugprofil
- Einträge + Dokumente/Nachweise
- Verifizierungslevel T1/T2/T3

### Sprint C – Public-QR + Kommunikation
- Public-QR Mini-Check (Ampel)
- Blogbase (Admin) + Newsletter
- Moderator-Akkreditierung + Begrenzungen

## 9) Offene Punkte / Annahmen (noch zu entscheiden)
- Exakte Definition T1/T2/T3 (Quelle/Beleg/Identität/Signatur?)
- Monetarisierung/Preise (Free/VIP/Dealer)
- Technischer Stack (rein static + API / Fullstack / Hosting)
- Export/Import (PDF, JSON, OEM-Schnittstellen)
