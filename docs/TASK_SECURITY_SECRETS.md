# Security: Production Secret-Manager Setup & Rotation

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** Security-Lead / Secrets Manager Admin  
**Deadline:** Bis **2026-03-03** (parallel zu DevOps Task)  
**Docs zum Lesen:** `docs/16_SECRETS_MANAGEMENT.md`

---

## Phase 1: Secret-Manager Option Evaluation & Entscheidung (Tag 1)

### 1.1 Vergleich der Optionen

| Kriterium | AWS Secrets Manager | Azure Key Vault | HashiCorp Vault | Self-Hosted |
|-----------|-------------------|-----------------|-----------------|-------------|
| **Setup-Time** | < 1h | < 1h | 4–8h | 4–8h |
| **Preis/Monat** | ~$0.40 + API calls | ~$0.15 + API calls | Self-hosted | Self-hosted |
| **Auto-Rotation** | Ja (via Lambdas) | Ja | Etwas komplex | Manuell |
| **IAM Integration** | Excellent (AWS) | Excellent (Azure) | Generic RBAC | Custom |
| **Compliance (ISO, SOC2)** | Ja | Ja | Ja | Ggf. nicht |
| **Best für AWS** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Best für Multi-Cloud** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Empfehlung:**
- **AWS-Only** → AWS Secrets Manager ✅ (schnellste Implementierung)
- **Multi-Cloud** → HashiCorp Vault (aber mehr Aufwand)
- **Zero-Cost** → Self-hosted Vault (aber operativer Overhead)

**Wir gehen mit:** `___________________________` (ausfüllen)

---

## Phase 2: Secrets Inventory & Generierung (Tag 1)

### 2.1 Secrets to Generate

Generiere und speichere folgende Secrets (SICHER!!!):

```bash
# LTC_SECRET_KEY (32+ Bytes, kryptographisch)
openssl rand -hex 32
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Database Admin Password (16+ Bytes)
openssl rand -hex 16
# Output: xyza1b2c3d4e5f6g7h8i9j0k1l2m3n4

# (Optional) Admin API Token
openssl rand -hex 32
# Output: ...
```

**Speichern in:** Sichere Passwort-Management-Tool
- [ ] 1Password / LastPass / Dashlane / Bitwarden
- [ ] ODER: Verschlüsselte Datei (z. B. mit `gpg`)
- [ ] NIEMALS: Plaintext, Email, Slack, unverschlüsselt

**Dokumentation Template:**

```
=== PRODUCTION SECRETS ===
Created: 2026-03-01 14:00 UTC
By: [Security-Lead Name]

LTC_SECRET_KEY:    a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
DB_ADMIN_PW:       xyza1b2c3d4e5f6g7h8i9j0k1l2m3n4
DB_USERNAME:       postgres
DB_HOST:           prod-db.cxxxxxx.eu-central-1.rds.amazonaws.com
DB_PORT:           5432
DB_NAME:           lifetimecircle_prod

Rotation Schedule:
  LTC_SECRET_KEY:  Quartalsweise (nächst: 2026-06-01)
  DB_ADMIN_PW:     Halbjährlich (nächst: 2026-09-01)
```

---

### 2.2 Secrets in AWS Secrets Manager speichern

Wenn AWS Secrets Manager gewählt:

```bash
# Login zu AWS
aws configure
# Gib Access Key, Secret Key ein

# 1. LTC_SECRET_KEY speichern
aws secretsmanager create-secret \
  --name prod/LTC_SECRET_KEY \
  --description "LifeTimeCircle Production JWT Secret" \
  --secret-string "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6" \
  --region eu-central-1

# Output:
# {
#     "ARN": "arn:aws:secretsmanager:eu-central-1:123456789:secret:prod/LTC_SECRET_KEY-aBcDe",
#     "Name": "prod/LTC_SECRET_KEY",
#     "VersionId": "aaa-111"
# }

# 2. Database URL speichern
aws secretsmanager create-secret \
  --name prod/DATABASE_URL \
  --description "PostgreSQL Connection String" \
  --secret-string "postgresql://postgres:ADMIN_PW@prod-db.cxxxxxx.eu-central-1.rds.amazonaws.com:5432/lifetimecircle_prod" \
  --region eu-central-1

# 3. Verifizieren (Abrufen)
aws secretsmanager get-secret-value \
  --secret-id prod/LTC_SECRET_KEY \
  --region eu-central-1

# Output JSON mit SecretString
```

**Dokumentieren:**
- [ ] Secret ARNs (alle 3+)
- [ ] SecretVersionId (für Audit)
- [ ] Region (z. B. eu-central-1)

---

### 2.3 IAM Policies für Prod-Server

Der Prod-Server (ECS Task / EC2 / Lambda) braucht Permissions zum Lesen der Secrets:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:eu-central-1:123456789:secret:prod/LTC_SECRET_KEY*",
        "arn:aws:secretsmanager:eu-central-1:123456789:secret:prod/DATABASE_URL*"
      ]
    }
  ]
}
```

**Steps in AWS IAM Console:**
- [ ] Neue Policy erstellen: "LifeTimeCircleProdSecretsRead"
- [ ] Obiges JSON einfügen
- [ ] Prodolving
- [ ] An "Prod-ECS-TaskRole" attachen

---

## Phase 3: Server-Integration (Tag 2)

### 3.1 Python-Anwendung (FastAPI)

Update `server/main.py`:

```python
import os
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_id: str) -> str:
    """Fetch secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='eu-central-1')
    try:
        response = client.get_secret_value(SecretId=secret_id)
        return response['SecretString']
    except ClientError as e:
        raise ValueError(f"Could not load secret {secret_id}: {e}")

# Load secrets in startup
SECRET_KEY = os.getenv('LTC_SECRET_KEY_LOCAL') or get_secret('prod/LTC_SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL') or get_secret('prod/DATABASE_URL')

# Validate
assert len(SECRET_KEY) >= 32, "SECRET_KEY too short"
assert DATABASE_URL.startswith('postgresql://'), "DATABASE_URL malformed"

print(f"✅ Loaded secrets (SECRET_KEY len={len(SECRET_KEY)})")
```

**Test lokal:**
```bash
# Mit lokal-gefälschtem SECRET_KEY
export LTC_SECRET_KEY_LOCAL="dev_test_secret_key_32_chars_minimum__OK"
python server/main.py
# → Sollte OK sein (greift auf lokal value zurück)

# Mit AWS Integration (ohne LOCAL_ override):
# (Braucht AWS credentials in Umgebung)
# → Würde von AWS abrufen
```

---

### 3.2 GitHub Actions CI/CD Integration

Update `.github/workflows/deploy-prod.yml`:

```yaml
name: Deploy Production

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-central-1
      
      - name: Load Secrets
        run: |
          # Diese Secrets werden im Workflow-Run temporarily geladen
          export LTC_SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id prod/LTC_SECRET_KEY --query SecretString --output text)
          export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id prod/DATABASE_URL --query SecretString --output text)
          # Diese env vars sind NUR für diese step verfügbar (nicht in logs!)
          
      - name: Build & Push
        run: |
          # AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY sind bereits im Runner
          bash ./tools/deploy_prod.sh
      
      - name: Verify
        run: |
          curl -X GET https://app.lifetimecircle.de/api/health
```

**Wichtig:** GitHub Secrets vs. AWS Secrets Manager unterscheidet:
- `${{ secrets.AWS_ACCESS_KEY_ID }}` = GitHub Secret (für CI zum Authentifizieren)
- `prod/LTC_SECRET_KEY` = AWS Secret (Production Runtime)

---

## Phase 4: Rotation & Audit Setup (Tag 2–3)

### 4.1 Manual Rotation Process

Quartalsweise (z. B. jeden 1. des Monats für März, Juni, Sept, Dez):

```bash
# 1. Neuen Secret generieren
NEW_SECRET=$(openssl rand -hex 32)

# 2. Den NEUEN Wert in AWS speichern
aws secretsmanager update-secret \
  --secret-id prod/LTC_SECRET_KEY \
  --secret-string "$NEW_SECRET" \
  --region eu-central-1

# 3. In Production deployen (neue Version wird geladen)
bash ./tools/deploy_prod.sh

# 4. Verifizieren
curl -X GET https://app.lifetimecircle.de/api/health

# 5. Dokumentieren (in Rotation Log)
echo "$(date): LTC_SECRET_KEY rotated. New version in AWS Secrets Manager." >> /var/log/lifetimecircle/secret_rotation.log
```

**Automatisierung (optional, später):**
- AWS Lambda + EventBridge = automatische Rotation
- Oder: Cronjob auf separatem Server für Rotation

---

### 4.2 Audit & Logging

AWS Secrets Manager logs automatisch zu CloudTrail:

```bash
# In AWS CloudTrail überprüfen: wer hat secrets gelesen?
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=prod/LTC_SECRET_KEY \
  --region eu-central-1 \
  --output table
```

**Alerting einrichten:**
- [ ] CloudWatch Alert: Falls Secret außerhalb normaler Arbeitszeiten gelesen wird
- [ ] CloudWatch Alert: Falls Secret in GitHub Actions außerhalb Deploy-Prozess gelesen wird
- [ ] Post diese Alerts an Security-Channel (Slack)

---

### 4.3 Kompromittierungs-Notfall

Falls Secret exposed (z. B. in GitHub, Log, etc.):

**Sofort (< 30 Min):**
1. Neuen Secret generieren
2. In AWS Secrets Manager updaten
3. Production re-deployen:
   ```bash
   aws ecs update-service --cluster prod --service api --force-new-deployment
   ```
4. Alte Session-Tokens invalidieren (falls JWT-based):
   ```sql
   DELETE FROM sessions WHERE created_at < NOW() - interval '1 hour';
   ```
5. Benutzer ggf. auffordern, neu zu authentifizieren

**Nach (1–2h):**
- [ ] Post-Mortem: Wie wurde Secret exposed?
- [ ] Git history scannen (falls in Commit)
- [ ] Logs scannen: Wurde Secret gelesen?
- [ ] Fix für commit hooks (pre-commit secret scanner)

---

## Phase 5: Dokumentation & Handoff (Tag 3)

### 5.1 Security Runbook

Erstelle `docs/SECRETS_PROD_RUNBOOK.md`:

```markdown
# Production Secrets Runbook

## Secrets Storage
- Location: AWS Secrets Manager, Region: eu-central-1
- Secrets:
  - prod/LTC_SECRET_KEY (ARN: arn:aws:...)
  - prod/DATABASE_URL (ARN: arn:aws:...)

## Access
- Only ECS Tasks via IAM Role: "LifeTimeCircleProdSecretsRead"
- Only GitHub Actions via AWS Access Keys

## Rotation Schedule
- LTC_SECRET_KEY: Quarterly (1st of month: Mar, Jun, Sep, Dec)
- DATABASE password: Semi-annual (Sep 1st)

## Emergency: Compromised Secret
1. Generate new secret value
2. Update in AWS Secrets Manager
3. Redeploy services
4. Invalidate sessions
5. Start post-mortem
```

### 5.2 Handoff to DevOps & SRE

Kommunizieren Sie:

- [ ] **An DevOps-Lead:**
  ```
  Secrets sind in AWS Secrets Manager.
  
  Secrets:
    - prod/LTC_SECRET_KEY: arn:aws:secretsmanager:eu-central-1:123456789:secret:prod/LTC_SECRET_KEY-xxxxx
    - prod/DATABASE_URL: arn:aws:secretsmanager:eu-central-1:123456789:secret:prod/DATABASE_URL-yyyyy
  
  IAM Role für Prod-Server: arn:aws:iam::123456789:role/LifeTimeCircleProdRole
  Policy attached: LifeTimeCircleProdSecretsRead
  
  Ready für Deployment.
  ```

- [ ] **An SRE-Lead:**
  ```
  Alerting für Secret-Access im CloudTrail sollte in euer Monitoring.
  
  Zielw rotation:
    - Mar 1, Jun 1, Sep 1, Dec 1 (LTC_SECRET_KEY)
    - Sep 1 (DB Password)
  
  Emergency contact: [Security-Lead Phone/Email/Slack]
  ```

---

## Checklist: Komplett

- [ ] Secret-Manager Option gewählt (AWS/Azure/Vault)
- [ ] Production Secrets generiert (LTC_SECRET_KEY, DB_PW, ...)
- [ ] Secrets in Secret Manager gespeichert (ARNs dokumentiert)
- [ ] IAM Policies erstellt & attached
- [ ] Server-Integration (Python/FastAPI) implementiert
- [ ] GitHub Actions CI/CD Integration aktualisiert
- [ ] Rotation-Plan dokumentiert
- [ ] Audit-Logging konfiguriert
- [ ] Emergency-Prozedur dokumentiert
- [ ] Runbooks erstellt
- [ ] Handoff an DevOps & SRE completed

---

## Deadline & Output

**Deadline:** **2026-03-03 EOD**

**Deliverables:**
- [ ] AWS Secrets Manager Secrets erstellt (3+)
- [ ] IAM Policy & Role konfiguriert
- [ ] `docs/SECRETS_PROD_RUNBOOK.md` erstellt
- [ ] Server-Code updated (boto3 integration)
- [ ] GitHub Actions Workflow updated
- [ ] Handoff-Email an DevOps/SRE (mit ARNs, Access-Info)
- [ ] Emergency-Kontakt-Info dokumentiert

---

**Wenn fertig → SRE kann parallel Monitoring setup!** ✅
