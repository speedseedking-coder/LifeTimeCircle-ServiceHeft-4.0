# Secrets Management – LifeTimeCircle Service Heft 4.0

Stand: **2026-03-01** (Europe/Berlin)

## Zweck
Dieses Dokument definiert, wie Geheimnisse (Secrets, API-Keys, Passwörter) sicher gespeichert, verwaltet und rotiert werden.

---

## 1) Secrets Inventory

### 1.1 Secrets, die LifeTimeCircle braucht

| Secret | Zweck | Länge | Rotation | Kritikalität |
|--------|-------|-------|----------|--------------|
| **LTC_SECRET_KEY** | Signing von JWTs, Session-Keys | ≥ 32 Bytes | quartalsweise | 🔴 Kritisch |
| **Database Password** | PostgreSQL Connection | ≥ 16 Bytes | halbjährlich | 🔴 Kritisch |
| **TLS Private Key** | HTTPS/SSL | – | auto (Let's Encrypt) | 🔴 Kritisch |
| **Admin API Token** (optional) | Maschinenbenutzer für Integr. | ≥ 32 Bytes | halbjährlich | 🟡 Wichtig |
| **External Service Keys** (optional) | z. B. Email-Service, SMS-Gateway | je nach Service | je nach Service | 🟡 Wichtig |

### 1.2 Was ist KEIN Secret?

```
❌ Environment: "production", "staging" (public Info)
❌ Version: "v1.0.0", "rc-2026-03-01" (Git-History)
❌ Config: Database-Host, API-Port (nicht sensitive)
✅ Aber: Wenn DB-Host intern ist → könnte auch Secret sein
```

---

## 2) Storage: Wo Secrets leben

### 2.1 Lokale Entwicklung

**Aktueller Stand (Repo):**
- `.gitignore` schließt `.env` aus ✅
- `server/tests/conftest.py` nutzt Fallback (`dev-key`) ✅
- Start-Skripte setzen Fallback-Keys ✅

**Best Practice lokal:**
```powershell
# .env.local (NICHT commetten!)
LTC_SECRET_KEY=dev_test_secret_key_32_chars_minimum__OK
DATABASE_URL=sqlite:///./data/app.db

# Laden in PowerShell
Get-Content .env.local | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path env:$name -Value $value
}
```

### 2.2 CI/CD (GitHub Actions)

**Aktueller Stand (Repo):**
- GitHub Secrets konfigurieren (Repo-Settings)
- `.github/workflows/ci.yml` nutzt sie ✅

**Anleitung zum Einrichten:**
1. GitHub Repo → Settings → Secrets and variables → Actions
2. New repository secret:
   - Name: `LTC_SECRET_KEY`
   - Value: `<generierter-64-char-string>`
3. In Workflow nutzen: `${{ secrets.LTC_SECRET_KEY }}`

**Code-Beispiel (aktuell):**
```yaml
env:
  LTC_SECRET_KEY: ${{ secrets.LTC_SECRET_KEY }}
```

### 2.3 Production (TBD – Entscheidung erforderlich)

| Lösung | Pros | Cons | Reife |
|--------|------|------|--------|
| **AWS Secrets Manager** | Managed, Auto-Rotation, IAM-Integration | Kostenpflichtig, AWS-abhängig | ⭐⭐⭐⭐⭐ |
| **Azure Key Vault** | Managed, Auto-Rotation, IAM | Azure-abhängig | ⭐⭐⭐⭐ |
| **HashiCorp Vault** | Universell, mächtig, Self-hosted | Komplexer zu betreiben | ⭐⭐⭐⭐ |
| **Environment Variables** | Einfach | Sichtbar in Prozess-Liste, nicht rotierbar | ⭐ |
| **Docker Secrets / Compose** | Für Dev OK | Production nicht ideal | ⭐⭐ |
| **.env Datei (encrypted)** | Einfach | Manuelle Rotation, Versionierung schwer | ⭐⭐ |

**Empfehlung für Production:** AWS Secrets Manager oder Azure Key Vault (falls bereits IaC vorhanden), ansonsten HashiCorp Vault.

---

## 3) Secret-Generierung

### 3.1 LTC_SECRET_KEY generieren

```bash
# Linux/Mac
openssl rand -hex 32

# PowerShell
[System.Convert]::ToBase64String([System.Random]::new().Next() * 1000000 | % {[byte]$_}) | 
  % {$_ -replace '[^a-zA-Z0-9]',''} | 
  select -First 32

# Oder: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Beispiel-Output:
# abc123def456ghi789jkl012mno345pq
```

### 3.2 Database Password generieren

```bash
# Ähnlich wie oben, mind. 16 Zeichen
openssl rand -hex 16

# Oder pw-manager: Dashlane, 1Password, Bitwarden
```

### 3.3 Sichere Speicherung (sofort nach Generierung)

```
✅ Screenshot/ Password Manager (verschlüsselt)
✅ Passwort-Manager (1Password, Bitwarden, LastPass)
✅ Secret Manager (AWS/Azure/Vault)
❌ Unverschlüsselt in Emails senden
❌ Plaintext in Docs/Wikis
❌ Slack/Teams (keine Enterprise-Backup)
```

---

## 4) Secrets in Code & Deployment

### 4.1 Python (FastAPI-Server)

**Aktuell (gut) ✅:**
```python
# Aus Umgebungsvariable laden
import os
SECRET_KEY = os.environ.get("LTC_SECRET_KEY") or "fallback-dev-key"

# Fallback nur für Dev/Test
if not SECRET_KEY or len(SECRET_KEY) < 16:
    raise ValueError("LTC_SECRET_KEY zu kurz!")
```

**Production (noch besser):**
```python
# Mit Pydantic Settings + Validation
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LTC_SECRET_KEY: str  # Pflicht!
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    class Config:
        env_file = ".env"  # optional, für lokal
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if len(self.LTC_SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY muss >= 32 zeichen sein")

settings = Settings()
# Wirft hier sofort Error wenn nicht valide!
```

### 4.2 React / Frontend

**Beachte:** Frontend hat direkten Browserzugriff!

```javascript
// ❌ FALSCH: Secrets ins Frontend builden
const API_SECRET = process.env.REACT_APP_SECRET_KEY;

// ✅ RICHTIG: Dynamisch vom Backend laden
async function getPublicConfig() {
  const resp = await fetch('/api/config/public');
  const data = await resp.json();
  return data.featuresEnabled; // OK: public info nur
}

// ✅ RICHTIG: Backend macht Auth, Frontend hat nur Token
const token = localStorage.getItem('auth_token');
fetch('/api/vehicles', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## 5) Secret-Rotation

### 5.1 Rotations-Plan

```
LTC_SECRET_KEY:
  Frequenz: Quartalsweise (alle 3 Monate)
  Grund: Best Practice für symmetrische Keys
  Vorankündigung: 2 Wochen
  
Database Password:
  Frequenz: Halbjährlich (alle 6 Monate)
  Grund: Standard-Sicherheit
  Methode: Neues Passwort setzen, Alte Sessions invalidieren
  
TLS Certificates:
  Frequenz: Auto via Let's Encrypt ✅
  Grund: Standard ACME-Renewal
  
Admin API Tokens:
  Frequenz: On-demand oder quartalsweise
  Grund: Falls kompromittiert oder regelmäßig
```

### 5.2 Rotation durchführen (LTC_SECRET_KEY)

```bash
# 1. NEUEN Key generieren
NEW_SECRET=$(openssl rand -hex 32)

# 2. Im Secret Manager speichern (z. B. AWS)
aws secretsmanager update-secret \
  --secret-id LTC_SECRET_KEY \
  --secret-string "$NEW_SECRET"

# 3. Oder in GitHub Secrets aktualisieren (Web UI)
# Settings → Secrets → LTC_SECRET_KEY → Update

# 4. Prod-Deployment auslösen (mit neuem Secret)
# CI/CD pipelines starten → Lädt den neuen Secret

# 5. Alte Sessions invalidieren (Optional)
# Falls alte Tokens noch gültig sind, manuell invalidieren:
# DELETE FROM sessions WHERE created_at < now() - interval '24 hours';

# 6. Verifizieren
curl -X GET https://app.lifetimecircle.de/api/health
# → 200 OK mit neuem Secret
```

### 5.3 Kompromittierte Secrets (NOTFALL)

```
Verdacht: Secret ist leaked/exposed

Sofort (< 1h):
1. Secret in Secret Manager inaktivieren/löschen
2. Neuen Secret generieren
3. Production redeploy mit neuem Secret
4. Logs auf verdächtige Zugriffe durchsuchen
5. Benutzer ggf. auffordern, neu zu authentifizieren

Nachher:
- Post-Mortem: Wie wurde das Secret exposed?
- Fix: Verhindere zukünftige Leaks
- Audit: Logs prüfen, wer hat was zugegriffen?
```

---

## 6) Zugriffskontrolle

### 6.1 Wer darf Secrets lesenaccess?

```
GitHub Secrets (für CI):
  ✅ Repository-Admin
  ✅ CI/CD-System (automatisch)
  ❌ Public (NIEMALS!)

AWS Secrets Manager / Azure Key Vault:
  ✅ Prod-Server (via IAM Role)
  ✅ DevOps-Lead
  ✅ Security-Lead
  ❌ Developer im Team (nur lokal dev-keys)

Production-Server:
  ✅ Deployment-Process (sudo, limited)
  ❌ SSH-User-Shell direkt (Secrets ausgelesen)
```

### 6.2 Audit & Logging

```
Jeden Secret-Zugriff loggen:
- Wer hat Secret-Manager aufgerufen?
- Wann?
- Welches Secret?
- Von wo (IP)?

In AWS:
- CloudTrail enabled
- Secret Manager API calls logged

Regelmäßig prüfen:
- Unerwartete Zugriffe?
- Alte Server noch Zugriff?
```

---

## 7) Checkliste: Bevor wir live gehen

- [ ] **LTC_SECRET_KEY** generiert (≥ 32 Bytes, kryptographisch stark)
- [ ] **GitHub Secrets** eingerichtet (LTC_SECRET_KEY + Database Password)
- [ ] **Production Secret Manager** gewählt und konfiguriert (AWS/Azure/Vault)
- [ ] **IAM Policies** eingerichtet (nur notwendige Services/Rollen lesen Secrets)
- [ ] **Rotation Plan** dokumentiert (Frequenz, Prozess, Tests)
- [ ] **Secret-Zugriff nicht hardcoded** in Code (alle aus Env-Variablen)
- [ ] **Audit-Logging** aktiviert (wer liest Secrets?)
- [ ] **Notfall-Plan** für kompromittierte Secrets dokumentiert
- [ ] **Team geschult** (wo nicht zu speichern, wie zu rotieren)

---

## 8) Referenzen

- `docs/14_DEPLOYMENT_GUIDE.md`
- `docs/15_MONITORING_INCIDENT_RESPONSE.md`
- `README.md` (Dev Setup mit Secret-Keys)
- `.github/workflows/ci.yml` (GitHub Secrets nutzen)
- OWASP: Secret Management Cheat Sheet
- NIST: Special Publication 800-57 (Key Management)

---

## 9) Notizen für Team

**Für Developers:**
- Lokale `.env` Datei mit Fallback-Keys ist OK
- `.env` wird nicht gecommittet (`.gitignore`)
- Niemals echte Production-Secrets lokal speichern!

**Für DevOps/SRE:**
- Production Secret Manager Setup **vor** Go-Live
- IAM Policies testen: Can prod-server read from secret-manager?
- Rotation-Automatisierung einrichten (wenn möglich)

**Für Security:**
- Regelmäßige Audits der Secret-Zugriffe
- Incident-Response für Leaks planen
- Pentests bedenken Secret-Management prüfen
