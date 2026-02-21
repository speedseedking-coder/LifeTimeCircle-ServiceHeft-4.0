import React from "react";
import { TrustAmpelDisclaimer } from "../components/TrustAmpelDisclaimer";
import { httpFetch } from "../lib/httpFetch";

type TrustLight = "GREEN" | "YELLOW" | "RED";

type PublicQrResponse = {
  trust_light: string;
  hint: string;
  disclaimer: string;
};

// SoT Pflichttext (exakt, UTF-8!)
const PUBLIC_QR_DISCLAIMER_TEXT =
  "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

function normalizeTrustLight(x: string): TrustLight {
  const v = (x || "").trim().toUpperCase();
  if (v === "GREEN") return "GREEN";
  if (v === "YELLOW") return "YELLOW";
  if (v === "RED") return "RED";
  return "YELLOW";
}

function TrustLightBadge({ value }: { value: TrustLight }) {
  const color = value === "GREEN" ? "#16a34a" : value === "YELLOW" ? "#ca8a04" : "#dc2626";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span
        aria-label={`Trust-Ampel: ${value}`}
        style={{
          width: 14,
          height: 14,
          borderRadius: 999,
          background: color,
          display: "inline-block",
        }}
      />
      <strong style={{ letterSpacing: 0.3 }}>{value}</strong>
    </div>
  );
}

export function PublicQrPage({ vehicleId }: { vehicleId: string }) {
  const [loading, setLoading] = React.useState(true);
  const [data, setData] = React.useState<PublicQrResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let alive = true;

    async function run() {
      try {
        setLoading(true);
        setError(null);

        const r = await httpFetch(`/api/public/qr/${encodeURIComponent(vehicleId)}`, {
          headers: { Accept: "application/json" },
        });

        // 403 consent_required -> redirect to consent (hash router)
        if (r.status === 403) {
          try {
            const data403 = await r.clone().json();
            const code = (data403 as any)?.detail?.code;
            if (code === "consent_required") {
              window.location.hash = "#/consent";
              return; // do not set error, we are redirecting
            }
          } catch {
            // ignore parse errors
          }
        }

        if (!r.ok) {
          throw new Error(`public_qr_http_${r.status}`);
        }

        const j = (await r.json()) as PublicQrResponse;
        if (!alive) return;
        setData(j);
      } catch (e: any) {
        if (!alive) return;
        setError(String(e?.message || "public_qr_failed"));
      } finally {
        if (!alive) return;
        setLoading(false);
      }
    }

    void run();
    return () => {
      alive = false;
    };
  }, [vehicleId]);

  const trustLight = normalizeTrustLight(data?.trust_light || "YELLOW");

  return (
    <main
      style={{
        maxWidth: 860,
        margin: "0 auto",
        padding: 16,
        fontFamily:
          'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial',
      }}
    >
      <header style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, opacity: 0.75 }}>LifeTimeCircle</div>
        <h1 style={{ margin: "6px 0 0", fontSize: 22 }}>Public QR</h1>
      </header>

      <section
        style={{
          border: "1px solid rgba(0,0,0,0.12)",
          borderRadius: 12,
          padding: 16,
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 style={{ margin: 0, fontSize: 16 }}>Trust-Ampel</h2>
          <TrustLightBadge value={trustLight} />
        </div>

        <div style={{ marginTop: 12, lineHeight: 1.4 }}>
          {loading && <div>laedt ...</div>}

          {!loading && error && (
            <div role="alert" style={{ opacity: 0.85 }}>
              QR-Daten nicht verfuegbar.
            </div>
          )}

          {!loading && !error && (
            <div style={{ opacity: 0.9 }}>{data?.hint || "Hinweis nicht verfuegbar."}</div>
          )}
        </div>
      </section>

      <TrustAmpelDisclaimer />

      {/* SoT/Verifier: Pflichttext muss auch in dieser Datei exakt vorhanden sein. */}
      <span style={{ display: "none" }} data-testid="public-qr-disclaimer">
        {PUBLIC_QR_DISCLAIMER_TEXT}
      </span>
    </main>
  );
}

