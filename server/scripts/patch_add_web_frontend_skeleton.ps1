# server/scripts/patch_add_web_frontend_skeleton.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir {
  param([Parameter(Mandatory = $true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-TextFile {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Content
  )
  $dir = Split-Path -Parent $Path
  if ($dir) { Ensure-Dir $dir }
  if (-not $Content.EndsWith("`n")) { $Content += "`n" }
  Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..") | Select-Object -ExpandProperty Path

$webRoot = Join-Path $repoRoot "packages\web"
$srcDir  = Join-Path $webRoot "src"

Ensure-Dir $webRoot
Ensure-Dir $srcDir

$files = @(
  @{
    Path    = (Join-Path $webRoot "package.json")
    Content = (@(
      '{',
      '  "name": "@lifetimecircle/web",',
      '  "private": true,',
      '  "version": "0.0.0",',
      '  "type": "module",',
      '  "scripts": {',
      '    "dev": "vite --host 127.0.0.1 --port 5173 --strictPort",',
      '    "build": "tsc -p tsconfig.json && vite build",',
      '    "preview": "vite preview --host 127.0.0.1 --port 5173 --strictPort"',
      '  },',
      '  "dependencies": {',
      '    "react": "^18.3.1",',
      '    "react-dom": "^18.3.1"',
      '  },',
      '  "devDependencies": {',
      '    "@types/react": "^18.3.12",',
      '    "@types/react-dom": "^18.3.1",',
      '    "@vitejs/plugin-react": "^4.3.4",',
      '    "typescript": "^5.6.3",',
      '    "vite": "^5.4.11"',
      '  }',
      '}'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot "vite.config.ts")
    Content = (@(
      'import { defineConfig } from "vite";',
      'import react from "@vitejs/plugin-react";',
      '',
      'export default defineConfig({',
      '  plugins: [react()],',
      '  server: {',
      '    host: "127.0.0.1",',
      '    port: 5173,',
      '    strictPort: true,',
      '    proxy: {',
      '      "/api": {',
      '        target: "http://127.0.0.1:8000",',
      '        changeOrigin: true,',
      '        rewrite: (path) => path.replace(/^\/api/, "")',
      '      }',
      '    }',
      '  }',
      '});'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot "tsconfig.json")
    Content = (@(
      '{',
      '  "compilerOptions": {',
      '    "target": "ES2022",',
      '    "useDefineForClassFields": true,',
      '    "lib": ["ES2022", "DOM", "DOM.Iterable"],',
      '    "module": "ESNext",',
      '    "skipLibCheck": true,',
      '',
      '    "moduleResolution": "Bundler",',
      '    "resolveJsonModule": true,',
      '    "isolatedModules": true,',
      '    "noEmit": true,',
      '    "jsx": "react-jsx",',
      '',
      '    "strict": true,',
      '    "noUnusedLocals": true,',
      '    "noUnusedParameters": true,',
      '    "noFallthroughCasesInSwitch": true',
      '  },',
      '  "include": ["src"]',
      '}'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot "tsconfig.node.json")
    Content = (@(
      '{',
      '  "compilerOptions": {',
      '    "target": "ES2022",',
      '    "lib": ["ES2022"],',
      '    "module": "ESNext",',
      '    "skipLibCheck": true,',
      '',
      '    "moduleResolution": "Bundler",',
      '    "resolveJsonModule": true,',
      '    "isolatedModules": true,',
      '    "noEmit": true,',
      '',
      '    "strict": true',
      '  },',
      '  "include": ["vite.config.ts"]',
      '}'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot "index.html")
    Content = (@(
      '<!doctype html>',
      '<html lang="de">',
      '  <head>',
      '    <meta charset="UTF-8" />',
      '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
      '    <title>LifeTimeCircle – Service Heft 4.0 (Web)</title>',
      '  </head>',
      '  <body>',
      '    <div id="root"></div>',
      '    <script type="module" src="/src/main.tsx"></script>',
      '  </body>',
      '</html>'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $srcDir "vite-env.d.ts")
    Content = (@(
      '/// <reference types="vite/client" />'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $srcDir "styles.css")
    Content = (@(
      ':root {',
      '  color-scheme: dark;',
      '  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";',
      '  line-height: 1.4;',
      '}',
      '',
      '* { box-sizing: border-box; }',
      '',
      'body {',
      '  margin: 0;',
      '  background: #0b0f14;',
      '  color: #e6edf3;',
      '}',
      '',
      'a { color: #7aa2f7; text-decoration: none; }',
      'a:hover { text-decoration: underline; }',
      '',
      '.container {',
      '  max-width: 980px;',
      '  margin: 0 auto;',
      '  padding: 24px 16px 56px;',
      '}',
      '',
      '.card {',
      '  background: rgba(255,255,255,0.04);',
      '  border: 1px solid rgba(255,255,255,0.08);',
      '  border-radius: 14px;',
      '  padding: 16px;',
      '  box-shadow: 0 8px 22px rgba(0,0,0,0.35);',
      '}',
      '',
      '.grid {',
      '  display: grid;',
      '  gap: 12px;',
      '  grid-template-columns: 1fr;',
      '}',
      '',
      '@media (min-width: 860px) {',
      '  .grid { grid-template-columns: 1fr 1fr; }',
      '}',
      '',
      '.h1 {',
      '  font-size: 22px;',
      '  margin: 0 0 10px 0;',
      '  letter-spacing: 0.2px;',
      '}',
      '',
      '.muted { color: rgba(230, 237, 243, 0.70); }',
      '',
      '.badge {',
      '  display: inline-flex;',
      '  gap: 8px;',
      '  align-items: center;',
      '  padding: 6px 10px;',
      '  border-radius: 999px;',
      '  border: 1px solid rgba(255,255,255,0.10);',
      '  background: rgba(0,0,0,0.25);',
      '  font-size: 13px;',
      '}',
      '',
      '.kv {',
      '  display: grid;',
      '  grid-template-columns: 160px 1fr;',
      '  gap: 8px 12px;',
      '  margin-top: 10px;',
      '  font-size: 14px;',
      '}',
      '',
      '.kv > div:nth-child(odd) { color: rgba(230, 237, 243, 0.70); }',
      '',
      'hr {',
      '  border: 0;',
      '  border-top: 1px solid rgba(255,255,255,0.10);',
      '  margin: 14px 0;',
      '}',
      '',
      'button {',
      '  appearance: none;',
      '  border: 1px solid rgba(255,255,255,0.12);',
      '  background: rgba(255,255,255,0.06);',
      '  color: #e6edf3;',
      '  padding: 9px 12px;',
      '  border-radius: 12px;',
      '  cursor: pointer;',
      '}',
      'button:hover { background: rgba(255,255,255,0.10); }',
      '',
      'pre {',
      '  margin: 0;',
      '  white-space: pre-wrap;',
      '  word-break: break-word;',
      '}'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $srcDir "main.tsx")
    Content = (@(
      'import React from "react";',
      'import ReactDOM from "react-dom/client";',
      'import App from "./App";',
      'import "./styles.css";',
      '',
      'ReactDOM.createRoot(document.getElementById("root")!).render(',
      '  <React.StrictMode>',
      '    <App />',
      '  </React.StrictMode>',
      ');'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $srcDir "App.tsx")
    Content = (@(
      'import React, { useCallback, useEffect, useMemo, useState } from "react";',
      '',
      'type HealthResult = {',
      '  ok: boolean;',
      '  detail?: string;',
      '  raw?: string;',
      '};',
      '',
      'async function fetchHealth(): Promise<HealthResult> {',
      '  const candidates = ["/api/health", "/api/public/site", "/api/docs", "/api/"];',
      '  for (const url of candidates) {',
      '    try {',
      '      const res = await fetch(url, { headers: { Accept: "application/json" } });',
      '      const text = await res.text();',
      '      if (!res.ok) {',
      '        continue;',
      '      }',
      '      try {',
      '        const json = JSON.parse(text);',
      '        return { ok: true, raw: JSON.stringify(json, null, 2) };',
      '      } catch {',
      '        return { ok: true, raw: text };',
      '      }',
      '    } catch {',
      '      // try next',
      '    }',
      '  }',
      '  return { ok: false, detail: "API nicht erreichbar via /api (Vite-Proxy)" };',
      '}',
      '',
      'export default function App() {',
      '  const [health, setHealth] = useState<HealthResult | null>(null);',
      '  const [loading, setLoading] = useState(false);',
      '  const [lastChecked, setLastChecked] = useState<string>("");',
      '',
      '  const nowIso = useMemo(() => new Date().toISOString(), []);',
      '  const apiBase = "http://127.0.0.1:8000";',
      '',
      '  const refresh = useCallback(async () => {',
      '    setLoading(true);',
      '    const r = await fetchHealth();',
      '    setHealth(r);',
      '    setLastChecked(new Date().toLocaleString("de-DE"));',
      '    setLoading(false);',
      '  }, []);',
      '',
      '  useEffect(() => {',
      '    void refresh();',
      '  }, [refresh]);',
      '',
      '  return (',
      '    <div className="container">',
      '      <div className="card">',
      '        <div className="h1">LifeTimeCircle – Service Heft 4.0 (Web)</div>',
      '        <div className="muted">',
      '          Vite läuft auf <b>127.0.0.1:5173</b>. Proxy: <b>/api → 127.0.0.1:8000</b>.',
      '        </div>',
      '',
      '        <hr />',
      '',
      '        <div className="grid">',
      '          <div className="card">',
      '            <div className="badge">',
      '              <span>API</span>',
      '              <b>{health ? (health.ok ? "OK" : "FAIL") : "…"}</b>',
      '            </div>',
      '',
      '            <div className="kv">',
      '              <div>Letzter Check</div>',
      '              <div>{lastChecked || "—"}</div>',
      '',
      '              <div>Proxy</div>',
      '              <div><code>/api</code></div>',
      '',
      '              <div>API Direct</div>',
      '              <div>',
      '                <a href={`${apiBase}/public/site`} target="_blank" rel="noreferrer">',
      '                  {apiBase}/public/site',
      '                </a>',
      '              </div>',
      '            </div>',
      '',
      '            <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>',
      '              <button onClick={() => void refresh()} disabled={loading}>',
      '                {loading ? "Prüfe…" : "Neu prüfen"}',
      '              </button>',
      '              <span className="muted" style={{ fontSize: 13 }}>',
      '                Build-Time: {nowIso}',
      '              </span>',
      '            </div>',
      '',
      '            {health?.detail && (',
      '              <div style={{ marginTop: 12 }} className="muted">',
      '                Detail: <code>{health.detail}</code>',
      '              </div>',
      '            )}',
      '',
      '            {health?.raw && (',
      '              <div style={{',
      '                marginTop: 12,',
      '                padding: 12,',
      '                background: "rgba(0,0,0,0.35)",',
      '                border: "1px solid rgba(255,255,255,0.08)",',
      '                borderRadius: 12',
      '              }}>',
      '                <pre>{health.raw}</pre>',
      '              </div>',
      '            )}',
      '          </div>',
      '',
      '          <div className="card">',
      '            <div className="badge">',
      '              <span>Links</span>',
      '            </div>',
      '',
      '            <div className="kv">',
      '              <div>Web</div>',
      '              <div><a href="http://127.0.0.1:5173" target="_blank" rel="noreferrer">http://127.0.0.1:5173</a></div>',
      '',
      '              <div>API /</div>',
      '              <div><a href={`${apiBase}/`} target="_blank" rel="noreferrer">{apiBase}/</a></div>',
      '',
      '              <div>API Docs</div>',
      '              <div><a href={`${apiBase}/docs`} target="_blank" rel="noreferrer">{apiBase}/docs</a></div>',
      '',
      '              <div>API ReDoc</div>',
      '              <div><a href={`${apiBase}/redoc`} target="_blank" rel="noreferrer">{apiBase}/redoc</a></div>',
      '            </div>',
      '',
      '            <hr />',
      '',
      '            <div className="muted" style={{ fontSize: 14 }}>',
      '              Wenn Web läuft, aber API-Check FAIL:',
      '              <ul>',
      '                <li>API läuft auf <code>127.0.0.1:8000</code></li>',
      '                <li>Vite Proxy ist aktiv (<code>/api</code>)</li>',
      '                <li>Firewall/AV blockiert Localhost nicht</li>',
      '              </ul>',
      '            </div>',
      '          </div>',
      '        </div>',
      '      </div>',
      '    </div>',
      '  );',
      '}'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot ".gitignore")
    Content = (@(
      'node_modules/',
      'dist/',
      '.vite/',
      '.DS_Store',
      '',
      '.env',
      '.env.*',
      '!.env.example',
      '',
      'npm-debug.log*',
      'yarn-debug.log*',
      'yarn-error.log*',
      'pnpm-debug.log*'
    ) -join "`n")
  },
  @{
    Path    = (Join-Path $webRoot "README.md")
    Content = (@(
      '# LifeTimeCircle – Service Heft 4.0 (Web)',
      '',
      '## Lokal starten',
      '',
      '```powershell',
      'cd .\packages\web',
      'npm install',
      'npm run dev',
      '```',
      '',
      '- Web: http://127.0.0.1:5173',
      '- API: http://127.0.0.1:8000',
      '',
      '## Proxy',
      '',
      '- Vite-Proxy: `/api/*` → `http://127.0.0.1:8000/*`',
      '- UI prüft `/api/health` und fällt zurück auf `/api/public/site`'
    ) -join "`n")
  }
)

foreach ($f in $files) {
  Write-TextFile -Path $f.Path -Content $f.Content
}

$pkg = Join-Path $webRoot "package.json"
if (-not (Test-Path -LiteralPath $pkg)) {
  throw "FAIL: package.json not created: $pkg"
}

Write-Host "OK: web frontend skeleton created under: $webRoot"
Write-Host "NEXT:"
Write-Host "  cd .\packages\web"
Write-Host "  npm install"
Write-Host "  npm run dev"
Write-Host "  Browser: http://127.0.0.1:5173"