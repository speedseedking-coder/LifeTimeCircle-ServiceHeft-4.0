
import { authHeaders, getAuthToken, isConsentRequired } from "../lib.auth";
import { useEffect, useMemo, useState } from "react";
import { apiGet, extractApiError, isRecord } from "../api";
import { createVehicle as createVehicleApi, createVehicleEntry } from "../vehiclesApi";

type WizardStep = 1 | 2 | 3;

type EntryDraft = {
  date: string;
  type: string;
  performedBy: string;
  km: string;
};

type WizardState = {
  step: WizardStep;
  vin: string;
  vehicleId: string | null;
  entryDraft: EntryDraft;
};

type GateState = "loading" | "allowed" | "forbidden";

const STORAGE_KEY = "ltc:onboarding:v1";
const today = new Date().toISOString().slice(0, 10);

const initialState: WizardState = {
  step: 1,
  vin: "",
  vehicleId: null,
  entryDraft: {
    date: today,
    type: "Service",
    performedBy: "Eigenleistung",
    km: "",
  },
};

function normalizeVin(raw: string): string {
  return raw.replace(/\s+/g, "").toUpperCase();
}

function maskVin(vin: string): string {
  const normalized = normalizeVin(vin);
  if (normalized.length <= 7) return "•••";
  return `${normalized.slice(0, 3)}••••••${normalized.slice(-4)}`;
}

function stepTitle(step: WizardStep): string {
  if (step === 1) return "VIN erfassen";
  if (step === 2) return "Fahrzeug anlegen";
  return "Ersten Entry anlegen";
}

function toApiErrorMessage(result: { error: string; body?: unknown; status: number }): string {
  const extracted = extractApiError(result.body);
  if (extracted) {
    if (result.status === 409 || result.status === 422) return `Bitte Eingaben prüfen: ${extracted}`;
    return extracted;
  }
  return `${result.error}${result.body ? `: ${String(result.body)}` : ""}`;
}

export default function OnboardingWizardPage(): JSX.Element {
  const [gate, setGate] = useState<GateState>("loading");
  const [wizard, setWizard] = useState<WizardState>(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  // restore draft
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<WizardState>;
      setWizard((prev) => ({
        ...prev,
        step: parsed.step === 2 || parsed.step === 3 ? parsed.step : 1,
        vin: typeof parsed.vin === "string" ? parsed.vin : prev.vin,
        vehicleId: typeof parsed.vehicleId === "string" ? parsed.vehicleId : null,
        entryDraft: {
          date: parsed.entryDraft?.date || prev.entryDraft.date,
          type: parsed.entryDraft?.type || prev.entryDraft.type,
          performedBy: parsed.entryDraft?.performedBy || prev.entryDraft.performedBy,
          km: parsed.entryDraft?.km || prev.entryDraft.km,
        },
      }));
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // consent gate
  useEffect(() => {
    let active = true;

    apiGet("/consent/status", { headers: authHeaders(getAuthToken()) }).then((res) => {
      if (!active) return;

      if (!res.ok) {
        const code = extractApiError(res.body);
        if (res.status === 401) {
          window.location.hash = "#/auth";
          return;
        }
        if (res.status === 403 && isConsentRequired(code)) {
          window.location.hash = "#/consent";
          return;
        }
        setGate("forbidden");
        setError(toApiErrorMessage(res));
        return;
      }

      const body = res.body;
      if (!isRecord(body)) {
        setGate("forbidden");
        setError("Consent-Status konnte nicht verarbeitet werden.");
        return;
      }

      const isComplete = Boolean(body.is_complete);
      if (!isComplete) {
        window.location.hash = "#/consent";
        return;
      }

      setGate("allowed");
    });

    return () => {
      active = false;
    };
  }, []);

  // persist draft
  useEffect(() => {
    if (gate !== "allowed" || done) return;
    const h = window.setTimeout(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(wizard));
    }, 200);
    return () => window.clearTimeout(h);
  }, [gate, wizard, done]);

  const vinValidation = useMemo(() => {
    const v = normalizeVin(wizard.vin);
    if (!v) return "VIN ist erforderlich.";
    if (v.length < 6) return "VIN ist zu kurz.";
    return null;
  }, [wizard.vin]);

  const kmValidation = useMemo(() => {
    if (wizard.entryDraft.km.trim().length === 0) return "Kilometerstand ist erforderlich.";
    const n = Number(wizard.entryDraft.km);
    if (!Number.isFinite(n) || n < 0) return "Kilometerstand muss >= 0 sein.";
    return null;
  }, [wizard.entryDraft.km]);

  async function onCreateVehicle() {
    if (vinValidation) {
      setError(vinValidation);
      return;
    }

    setSubmitting(true);
    setError(null);

    const res = await createVehicleApi({ vin: normalizeVin(wizard.vin) }, { headers: authHeaders(getAuthToken()) });

    if (!res.ok) {
      const code = extractApiError(res.body);
      if (res.status === 401) {
        window.location.hash = "#/auth";
        return;
      }
      if (res.status === 403 && isConsentRequired(code)) {
        window.location.hash = "#/consent";
        return;
      }
      setError(toApiErrorMessage(res));
      setSubmitting(false);
      return;
    }

    const vehicleId = res.body.id;
    if (!vehicleId) {
      setError("Fahrzeug wurde erstellt, aber die Antwort enthält keine vehicleId.");
      setSubmitting(false);
      return;
    }

    setWizard((prev) => ({ ...prev, step: 3, vehicleId }));
    setSubmitting(false);
  }

  async function createFirstEntry() {
    if (!wizard.vehicleId) {
      setError("Fahrzeug-ID fehlt. Bitte Schritt 2 erneut ausführen.");
      return;
    }
    if (kmValidation) {
      setError(kmValidation);
      return;
    }

    setSubmitting(true);
    setError(null);

    const res = await createVehicleEntry(
      wizard.vehicleId,
      {
        date: wizard.entryDraft.date,
        type: wizard.entryDraft.type,
        performed_by: wizard.entryDraft.performedBy,
        km: Number(wizard.entryDraft.km),
      },
      { headers: authHeaders(getAuthToken()) },
    );

    if (!res.ok) {
      const code = extractApiError(res.body);
      if (res.status === 401) {
        window.location.hash = "#/auth";
        return;
      }
      if (res.status === 403 && isConsentRequired(code)) {
        window.location.hash = "#/consent";
        return;
      }
      setError(toApiErrorMessage(res));
      setSubmitting(false);
      return;
    }

    localStorage.removeItem(STORAGE_KEY);
    setDone(true);
    setSubmitting(false);
  }

  function restart() {
    localStorage.removeItem(STORAGE_KEY);
    setDone(false);
    setError(null);
    setWizard({ ...initialState, entryDraft: { ...initialState.entryDraft, date: today } });
  }

  if (gate === "loading") {
    return (
      <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
        <h1>Onboarding Wizard</h1>
        <p>Consent wird geprüft…</p>
      </main>
    );
  }

  if (gate === "forbidden") {
    return (
      <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
        <h1>Onboarding Wizard</h1>
        <p>Der Wizard ist aktuell nicht verfügbar.</p>
        {error ? <p style={{ color: "#fca5a5" }}>{error}</p> : null}
        <a href="#/auth">Zurück zu Auth</a>
      </main>
    );
  }

  if (done && wizard.vehicleId) {
    return (
      <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
        <h1>Geschafft 🎉</h1>
        <p>Fahrzeug und erster Entry wurden erfolgreich angelegt.</p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
          <a
            href={`#/vehicles/${encodeURIComponent(wizard.vehicleId)}`}
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              border: "1px solid rgba(122,162,247,0.7)",
              background: "rgba(122,162,247,0.18)",
            }}
          >
            Zum Fahrzeug
          </a>
          <a href="#/documents">Dokument hochladen</a>
          <a href={`#/vehicles/${encodeURIComponent(wizard.vehicleId)}`}>Weitere Einträge</a>
        </div>
        <div style={{ marginTop: 16 }}>
          <button type="button" onClick={restart}>
            Neu starten
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Onboarding Wizard</h1>
      <p>In wenigen Schritten zum ersten belastbaren Nachweis: Fahrzeug anlegen und ersten Entry speichern.</p>

      <ol style={{ display: "flex", gap: 12, paddingLeft: 20 }}>
        <li style={{ opacity: wizard.step === 1 ? 1 : 0.7 }}>VIN</li>
        <li style={{ opacity: wizard.step === 2 ? 1 : 0.7 }}>Fahrzeug</li>
        <li style={{ opacity: wizard.step === 3 ? 1 : 0.7 }}>Erster Entry</li>
      </ol>

      <h2>{stepTitle(wizard.step)}</h2>

      {wizard.step === 1 ? (
        <section>
          <label htmlFor="vin-input">VIN</label>
          <input
            id="vin-input"
            value={wizard.vin}
            onChange={(e) => setWizard((prev) => ({ ...prev, vin: e.target.value }))}
            placeholder="z. B. WAUZZZ..."
            autoComplete="off"
            style={{ display: "block", marginTop: 8, padding: 8, width: "100%", maxWidth: 420 }}
          />
          <p style={{ marginTop: 8, opacity: 0.85 }}>
            Warum VIN? Wir nutzen die VIN nur zur eindeutigen Zuordnung. Public wird sie maskiert angezeigt.
          </p>
          {vinValidation ? <p style={{ color: "#fca5a5" }}>{vinValidation}</p> : null}
          <button
            type="button"
            onClick={() => setWizard((prev) => ({ ...prev, step: 2, vin: normalizeVin(prev.vin) }))}
            disabled={Boolean(vinValidation)}
          >
            Weiter
          </button>
        </section>
      ) : null}

      {wizard.step === 2 ? (
        <section>
          <p>
            VIN erfasst: <code>{maskVin(wizard.vin)}</code>
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" onClick={() => setWizard((prev) => ({ ...prev, step: 1 }))} disabled={submitting}>
              Zurück
            </button>
            <button type="button" onClick={onCreateVehicle} disabled={submitting || Boolean(vinValidation)}>
              {submitting ? "Speichert…" : "Fahrzeug speichern"}
            </button>
          </div>
        </section>
      ) : null}

      {wizard.step === 3 ? (
        <section>
          <div style={{ display: "grid", gap: 10, maxWidth: 420 }}>
            <label>
              Datum
              <input
                type="date"
                value={wizard.entryDraft.date}
                onChange={(e) => setWizard((prev) => ({ ...prev, entryDraft: { ...prev.entryDraft, date: e.target.value } }))}
              />
            </label>
            <label>
              Typ
              <input
                type="text"
                value={wizard.entryDraft.type}
                onChange={(e) => setWizard((prev) => ({ ...prev, entryDraft: { ...prev.entryDraft, type: e.target.value } }))}
              />
            </label>
            <label>
              Durchgeführt von
              <input
                type="text"
                value={wizard.entryDraft.performedBy}
                onChange={(e) =>
                  setWizard((prev) => ({ ...prev, entryDraft: { ...prev.entryDraft, performedBy: e.target.value } }))
                }
              />
            </label>
            <label>
              Kilometerstand
              <input
                type="number"
                min={0}
                value={wizard.entryDraft.km}
                onChange={(e) => setWizard((prev) => ({ ...prev, entryDraft: { ...prev.entryDraft, km: e.target.value } }))}
              />
            </label>
          </div>

          {kmValidation ? <p style={{ color: "#fca5a5" }}>{kmValidation}</p> : null}

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button type="button" onClick={() => setWizard((prev) => ({ ...prev, step: 2 }))} disabled={submitting}>
              Zurück
            </button>
            <button
              type="button"
              onClick={createFirstEntry}
              disabled={
                submitting ||
                Boolean(kmValidation) ||
                wizard.entryDraft.date.trim().length === 0 ||
                wizard.entryDraft.type.trim().length === 0 ||
                wizard.entryDraft.performedBy.trim().length === 0
              }
            >
              {submitting ? "Speichert…" : "Entry speichern"}
            </button>
          </div>
        </section>
      ) : null}

      {error ? (
        <section style={{ marginTop: 14 }}>
          <p style={{ color: "#fca5a5" }}>{error}</p>
          <button type="button" onClick={() => setError(null)}>
            Fehler schließen
          </button>
        </section>
      ) : null}
    </main>
  );
}
