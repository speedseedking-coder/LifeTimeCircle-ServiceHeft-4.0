\# Dateiname: docs/routine/00\_PROJECT\_BRIEF.md

\# LifeTimeCircle – Service Heft 4.0 · Project Brief

Version: 2026-03 | Last-Update: YYYY-MM-DD



\## 1) Ziel

Produktionsreife Plattform (keine Demo) für den digitalen Fahrzeug-Lebenslauf:

Service-/Wartungs-/Ereignishistorie + Nachweise, QR-Fahrzeug-ID, Public-QR Trustscore (Ampel).



\## 2) Branding / Benennung (fix)

\- Brand: \*\*LifeTimeCircle\*\*

\- Produkt/Modul: \*\*Service Heft 4.0\*\*

\- Kontakt: \*\*lifetimecircle@online.de\*\*

\- Canonical Docs (Source of Truth): `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs`



\## 3) Nicht-Ziele (klar abgrenzen)

\- Public-QR ist \*\*keine\*\* technische Zustandsbewertung.

\- Keine Public-Ausgabe von Metrics/Counts/Percentages/Zeiträumen.

\- Keine “Demo-Shortcuts” (Security/Privacy/RBAC sind verbindlich).



\## 4) Kernfeatures (MVP)

1\) \*\*Auth\*\*: E-Mail Login + Verifizierung (One-time + TTL + Rate-Limits + Anti-Enumeration)  

2\) \*\*Consent\*\*: AGB+Datenschutz Pflicht, Version+Timestamp speichern  

3\) \*\*RBAC\*\*: serverseitig enforced, deny-by-default, least privilege  

4\) \*\*Service Heft\*\*: Fahrzeug + Einträge + Nachweise (T1/T2/T3)  

5\) \*\*QR-Fahrzeug-ID\*\*: Public-QR Mini-Check + (Login-Bereich) ServiceHeft  

6\) \*\*Public-QR Trustscore\*\*: Rot/Orange/Gelb/Grün + Gründe + Disclaimer (ohne Metrics)  

7\) \*\*VIP/Dealer Transfer\*\*: Übergabe-QR / interner Verkauf nur VIP/DEALER  

8\) \*\*Blog/News + Newsletter\*\*: Admin erstellt; Moderator nur Blog/News



\## 5) Harte Produktregeln

\- Public-QR bewertet ausschließlich \*\*Nachweis-/Dokumentationsqualität\*\*, niemals technischen Zustand.

\- Verkauf/Übergabe-QR \& interner Verkauf: \*\*nur VIP \& DEALER (gewerblich)\*\*.

\- VIP-Gewerbe: \*\*max 2 Staff\*\*, Freigabe nur \*\*SUPERADMIN\*\*.

\- MODERATOR: \*\*nur Blog/News\*\*, keine PII, kein Export, kein Audit-Zugriff.



\## 6) Qualitätsziel / DoD (Kurz)

\- Navigation/Buttons ok, Empty States ok

\- RBAC serverseitig, Public-QR ohne Metrics + Disclaimer

\- Logs/Audit/Export konform, keine Secrets/PII im Log

\- Uploads: allowlist + quarantine by default



