import { useEffect, useMemo, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import {
  acceptRequiredConsents,
  buildConsentAcceptances,
  fetchConsentStatus,
  fetchRequiredConsents,
  normalizeAcceptedConsents,
  normalizeRequiredConsents,
  type ConsentAcceptance,
  type RequiredConsent,
} from "../authConsentApi";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";

type ViewState = "loading" | "ready" | "saving" | "error";

function safeNextHash(raw: string | null): string {
  if (!raw || !raw.startsWith("#/") || raw.startsWith("#//")) return "#/vehicles";
  return raw;
}

function nextHashFromLocation(): string {
  const raw = window.location.hash || "#/consent";
  const query = raw.split("?")[1] ?? "";
  const params = new URLSearchParams(query);
  return safeNextHash(params.get("next"));
}

function acceptedMap(accepted: ConsentAcceptance[]): Record<string, ConsentAcceptance> {
  const out: Record<string, ConsentAcceptance> = {};
  for (const item of accepted) {
    out[`${item.doc_type}:${item.doc_version}`] = item;
  }
  return out;
}

export default function ConsentPage(): JSX.Element {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [requiredConsents, setRequiredConsents] = useState<RequiredConsent[]>([]);
  const [acceptedConsents, setAcceptedConsents] = useState<ConsentAcceptance[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [termsChecked, setTermsChecked] = useState(false);
  const [privacyChecked, setPrivacyChecked] = useState(false);
  const [error, setError] = useState("");

  const nextHash = useMemo(() => nextHashFromLocation(), []);
  const acceptedByKey = useMemo(() => acceptedMap(acceptedConsents), [acceptedConsents]);

  useEffect(() => {
    let alive = true;

    const run = async () => {
      const token = getAuthToken();
      if (!token) {
        handleUnauthorized();
        return;
      }

      setViewState("loading");
      setError("");

      const headers = authHeaders(token);
      const [currentRes, statusRes] = await Promise.all([fetchRequiredConsents(), fetchConsentStatus(headers)]);
      if (!alive) return;

      if (!currentRes.ok) {
        setViewState("error");
        setError("Erforderliche Consent-Versionen konnten nicht geladen werden.");
        return;
      }

      if (!statusRes.ok) {
        if (statusRes.status === 401) {
          handleUnauthorized();
          return;
        }
        if (statusRes.status === 403) {
          setViewState("error");
          setError("Consent-Status ist für die aktuelle Rolle oder Session nicht verfügbar.");
          return;
        }
        setViewState("error");
        setError("Consent-Status konnte nicht geladen werden.");
        return;
      }

      const required = normalizeRequiredConsents(currentRes.body);
      if (required.length === 0) {
        setViewState("error");
        setError("Consent-Discovery liefert kein nutzbares Format.");
        return;
      }

      const accepted = normalizeAcceptedConsents(statusRes.body);
      const complete = !!(statusRes.body && typeof statusRes.body === "object" && (statusRes.body as { is_complete?: unknown }).is_complete === true);
      const map = acceptedMap(accepted);

      setRequiredConsents(required);
      setAcceptedConsents(accepted);
      setIsComplete(complete);
      setTermsChecked(required.some((item) => item.doc_type === "terms" && !!map[`${item.doc_type}:${item.doc_version}`]));
      setPrivacyChecked(required.some((item) => item.doc_type === "privacy" && !!map[`${item.doc_type}:${item.doc_version}`]));
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, []);

  async function onAccept() {
    const token = getAuthToken();
    if (!token) {
      handleUnauthorized();
      return;
    }

    if (!termsChecked || !privacyChecked) {
      setError("Bitte Terms und Privacy bestätigen.");
      return;
    }

    setViewState("saving");
    setError("");

    const headers = authHeaders(token);
    const payload = buildConsentAcceptances(requiredConsents);
    const res = await acceptRequiredConsents(payload, headers);

    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setViewState("error");
      setError("Consent konnte nicht gespeichert werden.");
      return;
    }

    const acceptedNow = buildConsentAcceptances(requiredConsents);
    setAcceptedConsents(acceptedNow);
    setIsComplete(true);
    setViewState("ready");
  }

  function goNext() {
    window.location.hash = nextHash;
  }

  return (
    <main style={{ padding: 12 }}>
      <h1>Consent</h1>
      <p>Anzeige und Speicherung der aktuell erforderlichen Terms-/Privacy-Versionen über `/consent/current`, `/consent/status` und `/consent/accept`.</p>

      <section className="ltc-card" style={{ marginTop: 16 }}>
        <h2>Flow</h2>
        <p className="ltc-muted">
          Nächster Zielbereich nach erfolgreichem Consent: <code>{nextHash}</code>
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button type="button" onClick={goNext} disabled={!isComplete}>
            Weiter
          </button>
          <a href="#/auth">Zurück zu Auth</a>
        </div>
      </section>

      {viewState === "loading" ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <div className="ltc-muted">Consent-Status wird geladen...</div>
        </section>
      ) : null}

      {viewState !== "loading" ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <h2>Erforderliche Dokumente</h2>

          {requiredConsents.length === 0 ? <p className="ltc-muted">Keine erforderlichen Dokumente gefunden.</p> : null}

          {requiredConsents.length > 0 ? (
            <ul>
              {requiredConsents.map((item) => {
                const key = `${item.doc_type}:${item.doc_version}`;
                const accepted = acceptedByKey[key];

                return (
                  <li key={key} style={{ marginBottom: 12 }}>
                    <strong>{item.doc_type}</strong> <code>{item.doc_version}</code>
                    {accepted ? (
                      <span className="ltc-muted">
                        {" "}
                        · akzeptiert am {new Date(accepted.accepted_at).toLocaleString("de-DE")}
                      </span>
                    ) : (
                      <span className="ltc-muted"> · noch nicht akzeptiert</span>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : null}
        </section>
      ) : null}

      {viewState !== "loading" && requiredConsents.length > 0 ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <h2>Akzeptieren</h2>
          <div style={{ display: "grid", gap: 10 }}>
            <label>
              <input type="checkbox" checked={termsChecked} onChange={(e) => setTermsChecked(e.target.checked)} /> Terms in aktueller Version
              akzeptieren
            </label>
            <label>
              <input type="checkbox" checked={privacyChecked} onChange={(e) => setPrivacyChecked(e.target.checked)} /> Privacy in aktueller
              Version akzeptieren
            </label>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
            <button type="button" disabled={viewState === "saving"} onClick={() => void onAccept()}>
              {viewState === "saving" ? "Speichert..." : isComplete ? "Erneut speichern" : "Consent speichern"}
            </button>
            <button type="button" onClick={goNext} disabled={!isComplete}>
              Weiter zum Zielbereich
            </button>
          </div>

          <p className="ltc-muted" style={{ marginTop: 10 }}>
            Status: {isComplete ? "aktuell" : "unvollständig"}
          </p>
        </section>
      ) : null}

      {error ? <InlineErrorBanner message={error} /> : null}

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href="#/auth">Zurück zu Auth</a>
          </li>
          <li>
            <a href={nextHash}>Zum Zielbereich</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
