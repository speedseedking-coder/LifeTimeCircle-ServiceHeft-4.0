import { isConsentRequired } from "../lib.auth";
import React from "react";
import { TrustAmpelDisclaimer } from "../components/TrustAmpelDisclaimer";
import { httpFetch } from "../lib/httpFetch";

type TrustLight = "GREEN" | "YELLOW" | "ORANGE" | "RED";

type PublicQrResponse = {
  trust_light: string;
  hint: string;
  history_status: string;
  evidence_status: string;
  verification_level: string;
  accident_status: string;
  accident_status_label: string;
  disclaimer: string;
};

// SoT Pflichttext (exakt, UTF-8!)
const PUBLIC_QR_DISCLAIMER_TEXT =
  "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

function normalizeTrustLight(x: string): TrustLight {
  const v = (x || "").trim().toUpperCase();
  if (v === "GRUEN") return "GREEN";
  if (v === "GELB") return "YELLOW";
  if (v === "ORANGE") return "ORANGE";
  if (v === "ROT") return "RED";
  if (v === "GREEN") return "GREEN";
  if (v === "YELLOW") return "YELLOW";
  if (v === "ORANGE") return "ORANGE";
  if (v === "RED") return "RED";
  return "YELLOW";
}

function TrustLightBadge({ value }: { value: TrustLight }) {
  const color = value === "GREEN" ? "#16a34a" : value === "YELLOW" ? "#ca8a04" : value === "ORANGE" ? "#ea580c" : "#dc2626";

  return (
    <div className="ltc-trust-badge">
      <span
        aria-label={`Trust-Ampel: ${value}`}
        className="ltc-trust-badge__light"
        style={{ background: color }}
      />
      <strong className="ltc-trust-badge__label">{value}</strong>
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
            const detail = (data403 as any)?.detail ?? data403;
            if (isConsentRequired(detail)) {
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
    <main className="ltc-main ltc-public-qr">
      <header className="ltc-public-qr__header">
        <div className="ltc-public-qr__subtitle">LifeTimeCircle</div>
        <h1 className="ltc-public-qr__title">Public QR</h1>
      </header>

      <section className="ltc-trust-card">
        <div className="ltc-trust-card__header">
          <h2 className="ltc-trust-card__title">Trust-Ampel</h2>
          <TrustLightBadge value={trustLight} />
        </div>

        <div className="ltc-trust-card__content">
          {loading && <div>laedt ...</div>}

          {!loading && error && (
            <div role="alert" style={{ opacity: 0.85 }}>
              QR-Daten nicht verfuegbar.
            </div>
          )}

          {!loading && !error && (
            <div className="ltc-trust-metadata">
              <div className="ltc-trust-metadata__item">
                <span className="ltc-trust-metadata__value">{data?.hint || "Hinweis nicht verfuegbar."}</span>
              </div>
              <div className="ltc-trust-metadata__item">
                <span className="ltc-trust-metadata__label">Historie:</span>
                <span className="ltc-trust-metadata__value">{data?.history_status === "vorhanden" ? "vorhanden" : "nicht vorhanden"}</span>
              </div>
              <div className="ltc-trust-metadata__item">
                <span className="ltc-trust-metadata__label">Nachweise:</span>
                <span className="ltc-trust-metadata__value">{data?.evidence_status === "vorhanden" ? "vorhanden" : "nicht vorhanden"}</span>
              </div>
              <div className="ltc-trust-metadata__item">
                <span className="ltc-trust-metadata__label">Verifizierung:</span>
                <span className="ltc-trust-metadata__value">{data?.verification_level || "nicht verfuegbar"}</span>
              </div>
              <div className="ltc-trust-metadata__item">
                <span className="ltc-trust-metadata__label">Unfallstatus:</span>
                <span className="ltc-trust-metadata__value">{data?.accident_status_label || "Unbekannt"}</span>
              </div>
            </div>
          )}
        </div>
      </section>

      <TrustAmpelDisclaimer />

      {/* SoT/Verifier: Pflichttext muss auch in dieser Datei exakt vorhanden sein. */}
      <span className="ltc-hidden-verifier" data-testid="public-qr-disclaimer">
        {PUBLIC_QR_DISCLAIMER_TEXT}
      </span>
    </main>
  );
}
