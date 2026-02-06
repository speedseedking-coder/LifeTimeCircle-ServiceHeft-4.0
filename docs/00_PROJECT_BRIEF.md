# LifeTimeCircle – Service Heft 4.0
**Project Brief (Single Source of Truth)**  
Stand: 2026-01-29 (Europe/Berlin)

## 1) Kurzbeschreibung
**LifeTimeCircle** ist die Plattform.  
**Service Heft 4.0** ist das Kernprodukt: digitales, verifizierbares Lebenslauf-/Serviceheft für Fahrzeuge.

Kontakt: **lifetimecircle@online.de**

## 2) Leitplanken (non-negotiable)
- **Produktionsreif (keine Demo)**
- **deny-by-default + least privilege**
- **RBAC serverseitig enforced**
- **Keine Secrets/Klartext-PII in Logs/Exports** (Pseudonyme via **HMAC**)
- **Public-QR ohne Metriken** (keine Counts/Percentages/Zeiträume) + Disclaimer Pflicht-Copy

## 3) Public-QR Mini-Check
Ampel: Rot/Orange/Gelb/Grün – bewertet ausschließlich Dokumentations-/Nachweisqualität.  
**Pflicht-Disclaimer (Public, exakte Copy):**  
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

## 4) Rollen (high-level)
- public: nur Public-QR
- user: eigene Fahrzeuge/Einträge
- vip: erweitert, Übergabe/Verkauf möglich
- dealer: gewerblich, Übergabe/Verkauf möglich
- moderator: nur Blog/News (keine PII, kein Export, kein Audit)
- admin: Governance; Hochrisiko nur durch **superadmin**

Sonderregel: VIP-Gewerbe max 2 Staff, Freigabe nur SUPERADMIN.

## 5) Zugang / Anmeldung
- E-Mail Login + Verifizierung (OTP/Magic-Link) mit TTL, Rate-Limits, Anti-Enumeration
- AGB + Datenschutz Pflicht (Version + Timestamp speichern)

