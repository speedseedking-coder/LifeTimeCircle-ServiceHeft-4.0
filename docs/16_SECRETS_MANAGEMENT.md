# Secrets Management – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck

Dieses Dokument beschreibt das Secrets-Handling für den realistischen Go-Live-Pfad am **2026-03-06**. Das Repo erwartet derzeit klassische Umgebungsvariablen. Eine direkte Integration mit AWS Secrets Manager, Azure Key Vault oder `boto3` ist **nicht** Teil des Pflichtpfads.

## Benötigte Secrets und sensible Werte

| Name | Pflicht | Zweck |
|------|---------|-------|
| `LTC_SECRET_KEY` | Ja | Signatur- und Session-Secret |
| `LTC_DATABASE_URL` | Ja für absolute Pfade | SQLAlchemy-Verbindung zur SQLite-Datei |
| `LTC_DB_PATH` | Ja für Auth | Pfad zur SQLite-Datei für Auth-Komponenten |
| TLS-Zertifikat / Private Key | Ja | HTTPS |
| SMTP-Zugangsdaten | Optional | falls Mailer produktiv aktiv ist |

Für den aktuellen Go-Live ist **kein PostgreSQL-Passwort** erforderlich, solange Production auf SQLite läuft.

## Lokale Entwicklung

Beispiel für lokal oder Staging:

```powershell
LTC_SECRET_KEY=dev_test_secret_key_32_chars_minimum__OK
LTC_DATABASE_URL=sqlite+pysqlite:///./data/app.db
LTC_DB_PATH=./data/app.db
```

Keine `.env` oder Secret-Dateien committen.

## Production-Ablage

Für den Go-Live sind diese Varianten zulässig:

1. geschützte Env-Datei auf dem Host, z. B. `/etc/lifetimecircle/api.env`
2. Passwortmanager plus manuell gepflegte Env-Datei
3. externer Secret Store, **wenn** die Werte vor Prozessstart in Umgebungsvariablen injiziert werden

Nicht zulässig:

- Klartext im Repo
- Versand per Chat oder E-Mail
- ungeschützte Dateien mit offenen Dateirechten

## Empfohlenes Production-Format

```text
LTC_ENV=prod
LTC_SECRET_KEY=<REDACTED_32_PLUS_CHARS>
LTC_DATABASE_URL=sqlite+pysqlite:////var/lib/lifetimecircle/data/app.db
LTC_DB_PATH=/var/lib/lifetimecircle/data/app.db
```

Dateirechte für die Env-Datei:

```bash
chown root:root /etc/lifetimecircle/api.env
chmod 600 /etc/lifetimecircle/api.env
```

## Generierung

### `LTC_SECRET_KEY`

```bash
openssl rand -hex 32
```

Alternativ:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Keine Beispielwerte oder echte Secrets in Dokumente eintragen.

## Nutzung im Betrieb

Der API-Prozess liest die Werte direkt aus der Umgebung:

- `LTC_SECRET_KEY` ist Pflicht, sonst startet die API nicht
- `LTC_DATABASE_URL` steuert die Hauptdatenbank
- `LTC_DB_PATH` wird von Auth-Komponenten separat verwendet

Deshalb müssen `LTC_DATABASE_URL` und `LTC_DB_PATH` **auf dieselbe Datenbankdatei zeigen**.

## Rotation

### Standard

- `LTC_SECRET_KEY`: quartalsweise oder nach Incident
- TLS-Zertifikate: automatisiert erneuern oder rechtzeitig manuell
- SMTP-Zugangsdaten: bei Personalwechsel oder Provider-Änderung

### Ablauf bei `LTC_SECRET_KEY`

1. neuen Wert generieren
2. Env-Datei aktualisieren
3. API neu starten
4. `/api/health` prüfen
5. laufende Sessions als potenziell ungültig betrachten

## Incident-Fall

Wenn ein Secret kompromittiert ist:

1. Wert sofort ersetzen
2. Host- und Zugriffsprotokolle prüfen
3. API neu starten
4. Incident dokumentieren
5. Ursache beheben

## Offene Betriebsentscheidungen

Vor Go-Live festzuziehen:

- wo die Produktions-Env-Datei liegt
- wer Schreibzugriff darauf hat
- wer Rotation freigibt
- wie die Notfall-Erreichbarkeit der Security-Verantwortlichen aussieht
