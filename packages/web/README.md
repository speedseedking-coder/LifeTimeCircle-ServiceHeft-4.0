# LifeTimeCircle – Service Heft 4.0 (Web)

## Lokal starten

```powershell
cd .\packages\web
npm install
npm run dev
```

- Web: http://127.0.0.1:5173
- API: http://127.0.0.1:8000

## Proxy

- Vite-Proxy: `/api/*` → `http://127.0.0.1:8000/*`
- UI prüft `/api/health` und fällt zurück auf `/api/public/site`
