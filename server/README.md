\# LifeTimeCircle – ServiceHeft 4.0 (Server/API)



\## Lokal starten (Windows / PowerShell)



Voraussetzungen:

\- Python 3.12

\- Poetry installiert



Im Ordner `server`:



```powershell

$env:LTC\_SECRET\_KEY="dev-only-change-me"

poetry install

poetry run pytest

poetry run uvicorn app.main:app --reload



curl http://127.0.0.1:8000/health







