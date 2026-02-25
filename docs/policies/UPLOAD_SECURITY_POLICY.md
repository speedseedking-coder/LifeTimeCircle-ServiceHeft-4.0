// File: ./docs//policies//UPLOAD/_SECURITY/_POLICY.md



\# UPLOAD\_SECURITY\_POLICY – Uploads, Quarantäne, Scan, Freigabe



\*\*Stand:\*\* 2026-01-28 (Europe/Berlin)  

\*\*Prinzip:\*\* Allowlist + Quarantäne by default + least privilege



---



\## 1) Allowlist (MUST)

Zulässige Typen (Start):

\- PDF

\- JPG/JPEG

\- PNG



MUST:

\- Content-Type serverseitig validieren (nicht nur Client).

\- Datei-Header/Magic Bytes prüfen.

\- Größenlimit serverseitig enforce (z. B. 20 MB pro Datei; konfigurierbar).



---



\## 2) Quarantäne (MUST)

\- Jeder Upload landet initial in `quarantine\_status = QUARANTINED`.

\- Quarantäne-Dateien:

&nbsp; - nicht öffentlich

&nbsp; - nicht für user/vip/dealer abrufbar

&nbsp; - nur admin kann Quarantäne-Freigabe/Reject sehen/entscheiden (Policy-gated)



---



\## 3) Scan (MUST)

\- Malware Scan (ClamAV o. ä.) oder externer Scanner.

\- Ergebnis:

&nbsp; - CLEAN → eligible für Freigabe

&nbsp; - SUSPICIOUS → block + admin review

&nbsp; - FAILED → block, retry policy-limited



---



\## 4) Freigabe (MUST)

\- Freigabe nur wenn:

&nbsp; - Scan = CLEAN

&nbsp; - RBAC erlaubt (owner/org owner) oder admin approval (konfig)

\- Nach Freigabe:

&nbsp; - `quarantine\_status = APPROVED`

&nbsp; - Document wird gemäß Visibility sichtbar (private/org/shared), nie public



---



\## 5) Storage (MUST)

\- Objektstore mit encryption at rest.

\- Signed URLs (kurzlebig) oder Proxy-Streaming; nie public buckets.

\- File names nicht aus User Input übernehmen (random object keys).



---



\## 6) Metadaten \& PII (MUST)

\- Dateiname aus Upload nicht in Logs.

\- Dokumenttitel kann PII enthalten → CLASS\_CONFIDENTIAL; nicht im Audit (nur redacted).



---



\## 7) Audit (MUST)

\- UPLOAD\_RECEIVED, UPLOAD\_QUARANTINED, UPLOAD\_SCANNED\_\*, UPLOAD\_APPROVED/REJECTED

Siehe AUDIT\_SCOPE\_AND\_ENUMS.md



