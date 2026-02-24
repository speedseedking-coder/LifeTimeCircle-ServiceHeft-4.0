./docs/04_MODULE_CATALOG.md
# LifeTimeCircle – ServiceHeft 4.0
## Modul-Katalog (kanonisch)

Stand: 2026-01-29  
Zweck: Eindeutige Modulübersicht + Tier-Zuordnung (Free/VIP Normal/VIP Gewerbe).

---

## 1) Tiers
- **Free (Basic):** für alle Nutzer; keine KI-Wertermittlung; keine Werkstatt-/Betriebsprozesse.
- **VIP Normal (Privat/Sammler):** Premium für Privat/Sammler.
- **VIP Gewerbetreibende (Werkstatt/Handel/Dealer):** prozess-/werkstattlastig.

---

## 2) Module nach Tiers

### 2.1 Free (Basic)
- Autokauf-Co-Pilot (Container/Startpunkt; VIP-Module verborgen)
- Checklisten „Ankauf privat“ (nur Papier/PDF)
- QR-Fahrzeug-ID (primäre Fahrzeugidentität; Basis fürs Anlegen)
- Digitaler Fahrzeugschein „immer dabei“ (codiert/geschützt; nur eingeloggter User)
- Fahrzeugbewertung (ohne KI)
  - Freitext + Sprachbeschreibung + persönliche Eindrücke (Dokumentation)
  - Detailabfrage möglich, aber nur historisch-orientiert
  - Pflicht-Infotext: „Kein echter Fahrzeugwert. KI-Wertermittlung ist nicht Bestandteil der Free-Version.“
- Frontschadencheck „Front zerschossen“ (Spaß-App)

### 2.2 VIP Normal (Privat/Sammler)
- KI-Fahrzeugbewertung (KI-gestützt, detailliert; Freitext + Detailabfrage KI-unterstützt)
- Galerie-Sammler (Hypercars/Sport/Luxus/Oldtimer/Militaria; inkl. Unfall-/Reparatur-Dokuhistorie)
- Geräusch- & Schwingungsanalyse (Handyaufnahme/Sensorik)
- Frontschadencheck „Front zerschossen“ (weiterhin sichtbar)

### 2.3 VIP Gewerbetreibende (Werkstatt/Handel/Dealer)
- Direktannahme-Workflow
- **MasterClipboard (externes Modul-Repo)**  
  Pfad: `C:\Users\stefa\Projekte\LifeTimeCircle-Modules\masterclipboard\`  
  Spezifikation: `MODULE_SPEC.md` (im Modul-Repo)  
  Zweck: Fahrzeugannahme-Zentrale (Sprachaufnahme → Keywords/Kategorien → Triage → Monitor/Tafel)
- Mengen-/Mängelliste per Spracheingabe (Teil von MasterClipboard)
- Monitor-/Tafelansicht (Output aus MasterClipboard)
- GPS-Probefahrt-Nachweis (Google-Maps-Track; anonymisiert; Durchführer = Mitarbeiter-ID)
- OBD-Gateway-Integration (GPS-Probefahrt + OBD-Abfrage gekoppelt)
- OBD-Diagnose (einzeln)
- Händlernetzwerk / Weiterleitung
- Interner Fahrzeugankauf (nur ServiceHeft 4.0)
- Rechnungsprüfer
- Reimport-Identitätscheck
- VIN/WID-Eingabe & Validierung
- Lichteinstellungs-Check per Foto (Fahrzeugmitte / Fahrersitz)
- KI-Agenten (Assistenzautomation: Werkstattannahme, Prozesse, Gebrauchtwagenverkauf, ServiceHeft-4.0-Empfehlungen)

---

## 3) Rollen-/Feature-Sonderregeln (Reminder)
- Übergabe/Verkauf-QR & interner Verkauf: nur VIP/Dealer.
- Moderator: nur Blog/News; kein Export; kein Audit; keine PII.
- VIP-Gewerbe: max. 2 Mitarbeiterplätze; Freigabe nur SUPERADMIN.
