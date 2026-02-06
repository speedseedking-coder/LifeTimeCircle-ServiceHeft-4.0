import React, { useCallback, useEffect, useMemo, useState } from "react";

type HealthResult = {
  ok: boolean;
  detail?: string;
  raw?: string;
};

async function fetchHealth(): Promise<HealthResult> {
  const candidates = ["/api/health", "/api/public/site", "/api/docs", "/api/"];
  for (const url of candidates) {
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      const text = await res.text();
      if (!res.ok) {
        continue;
      }
      try {
        const json = JSON.parse(text);
        return { ok: true, raw: JSON.stringify(json, null, 2) };
      } catch {
        return { ok: true, raw: text };
      }
    } catch {
      // try next
    }
  }
  return { ok: false, detail: "API nicht erreichbar via /api (Vite-Proxy)" };
}

export default function App() {
  const [health, setHealth] = useState<HealthResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<string>("");

  const nowIso = useMemo(() => new Date().toISOString(), []);
  const apiBase = "http://127.0.0.1:8000";

  const refresh = useCallback(async () => {
    setLoading(true);
    const r = await fetchHealth();
    setHealth(r);
    setLastChecked(new Date().toLocaleString("de-DE"));
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="container">
      <div className="card">
        <div className="h1">LifeTimeCircle – Service Heft 4.0 (Web)</div>
        <div className="muted">
          Vite läuft auf <b>127.0.0.1:5173</b>. Proxy: <b>/api → 127.0.0.1:8000</b>.
        </div>

        <hr />

        <div className="grid">
          <div className="card">
            <div className="badge">
              <span>API</span>
              <b>{health ? (health.ok ? "OK" : "FAIL") : "…"}</b>
            </div>

            <div className="kv">
              <div>Letzter Check</div>
              <div>{lastChecked || "—"}</div>

              <div>Proxy</div>
              <div><code>/api</code></div>

              <div>API Direct</div>
              <div>
                <a href={`${apiBase}/public/site`} target="_blank" rel="noreferrer">
                  {apiBase}/public/site
                </a>
              </div>
            </div>

            <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
              <button onClick={() => void refresh()} disabled={loading}>
                {loading ? "Prüfe…" : "Neu prüfen"}
              </button>
              <span className="muted" style={{ fontSize: 13 }}>
                Build-Time: {nowIso}
              </span>
            </div>

            {health?.detail && (
              <div style={{ marginTop: 12 }} className="muted">
                Detail: <code>{health.detail}</code>
              </div>
            )}

            {health?.raw && (
              <div style={{
                marginTop: 12,
                padding: 12,
                background: "rgba(0,0,0,0.35)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 12
              }}>
                <pre>{health.raw}</pre>
              </div>
            )}
          </div>

          <div className="card">
            <div className="badge">
              <span>Links</span>
            </div>

            <div className="kv">
              <div>Web</div>
              <div><a href="http://127.0.0.1:5173" target="_blank" rel="noreferrer">http://127.0.0.1:5173</a></div>

              <div>API /</div>
              <div><a href={`${apiBase}/`} target="_blank" rel="noreferrer">{apiBase}/</a></div>

              <div>API Docs</div>
              <div><a href={`${apiBase}/docs`} target="_blank" rel="noreferrer">{apiBase}/docs</a></div>

              <div>API ReDoc</div>
              <div><a href={`${apiBase}/redoc`} target="_blank" rel="noreferrer">{apiBase}/redoc</a></div>
            </div>

            <hr />

            <div className="muted" style={{ fontSize: 14 }}>
              Wenn Web läuft, aber API-Check FAIL:
              <ul>
                <li>API läuft auf <code>127.0.0.1:8000</code></li>
                <li>Vite Proxy ist aktiv (<code>/api</code>)</li>
                <li>Firewall/AV blockiert Localhost nicht</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
