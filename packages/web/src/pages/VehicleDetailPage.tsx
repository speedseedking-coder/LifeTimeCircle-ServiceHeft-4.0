import { useEffect, useMemo, useState } from "react";
import ForbiddenPanel from "../components/ForbiddenPanel";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";
import {
  createVehicleEntry,
  createVehicleEntryRevision,
  getVehicle,
  getVehicleTrustSummary,
  getVehicleEntryHistory,
  listVehicleEntries,
  type Vehicle,
  type VehicleEntry,
  type VehicleTrustSummary,
} from "../vehiclesApi";

type ViewState = "loading" | "ready" | "forbidden" | "error";

type EntryDraft = {
  date: string;
  type: string;
  performed_by: string;
  km: string;
  note: string;
  cost_amount: string;
  trust_level: "" | "T1" | "T2" | "T3";
};

const today = new Date().toISOString().slice(0, 10);

function trustFoldersHref(vehicleId: string): string {
  return `#/trust-folders?vehicle_id=${encodeURIComponent(vehicleId)}&addon_key=restauration`;
}

function defaultDraft(): EntryDraft {
  return {
    date: today,
    type: "Service",
    performed_by: "Eigenleistung",
    km: "",
    note: "",
    cost_amount: "",
    trust_level: "",
  };
}

function safeNextHash(raw: string): string {
  if (!raw.startsWith("#/") || raw.startsWith("#//")) return "#/vehicles";
  return raw;
}

function toErrorCode(body: unknown): string {
  if (typeof body === "string") return body;
  if (body && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object" && typeof (detail as { code?: unknown }).code === "string") {
      return (detail as { code: string }).code;
    }
  }
  return "";
}

function toErrorMessage(result: { status: number; body?: unknown; error: string }): string {
  const code = toErrorCode(result.body);
  if (result.status === 404 && (code === "not_found" || code === "entry_not_found")) return "Fahrzeug oder Entry wurde nicht gefunden.";
  if (result.status === 403 && code === "consent_required") {
    const next = encodeURIComponent(safeNextHash(window.location.hash || "#/vehicles"));
    window.location.hash = `#/consent?next=${next}`;
    return "Consent erforderlich.";
  }
  if (result.status === 403 && code === "forbidden") return "Kein Zugriff auf dieses Fahrzeug.";
  return "Fahrzeugdetail konnte nicht geladen oder gespeichert werden.";
}

function normalizeDraft(draft: EntryDraft) {
  const km = Number(draft.km);
  if (!draft.date.trim()) return { ok: false as const, error: "Datum ist erforderlich." };
  if (!draft.type.trim()) return { ok: false as const, error: "Typ ist erforderlich." };
  if (!draft.performed_by.trim()) return { ok: false as const, error: "„Durchgeführt von“ ist erforderlich." };
  if (!Number.isFinite(km) || km < 0) return { ok: false as const, error: "Kilometerstand muss >= 0 sein." };

  const costRaw = draft.cost_amount.trim();
  let cost_amount: number | null = null;
  if (costRaw.length > 0) {
    const parsed = Number(costRaw.replace(",", "."));
    if (!Number.isFinite(parsed) || parsed < 0) return { ok: false as const, error: "Kostenbetrag muss >= 0 sein." };
    cost_amount = parsed;
  }

  return {
    ok: true as const,
    body: {
      date: draft.date,
      type: draft.type.trim(),
      performed_by: draft.performed_by.trim(),
      km,
      note: draft.note.trim() || null,
      cost_amount,
      trust_level: draft.trust_level || null,
    },
  };
}

function revisionLabel(entry: VehicleEntry): string {
  if (entry.revision_count <= 1) return "v1";
  return `v${entry.version} von ${entry.revision_count}`;
}

function trustLightLabel(value: VehicleTrustSummary["trust_light"] | null): string {
  if (value === "gruen") return "Gruen";
  if (value === "gelb") return "Gelb";
  if (value === "orange") return "Orange";
  if (value === "rot") return "Rot";
  return "Nicht verfuegbar";
}

function trustLevelMeaning(value: VehicleEntry["trust_level"] | null): string {
  if (value === "T3") return "Dokument vorhanden";
  if (value === "T2") return "Physisches Serviceheft vorhanden";
  if (value === "T1") return "Physisches Serviceheft nicht vorhanden";
  return "Nicht klassifiziert";
}

/* ========== VEHICLE ENRICHMENT STATISTICS ========== */

function trustLightColor(light: VehicleTrustSummary["trust_light"]): string {
  if (light === "gruen") return "#10b981"; // green
  if (light === "gelb") return "#fbbf24"; // amber
  if (light === "orange") return "#f97316"; // orange
  if (light === "rot") return "#ef4444"; // red
  return "#9ca3af"; // gray
}

type EntryStats = {
  totalEntries: number;
  totalCost: number;
  totalKmTraveled: number;
  firstEntryDate: string | null;
  lastEntryDate: string | null;
  minKm: number;
  maxKm: number;
  typeBreakdown: Record<string, number>;
  trustLevelBreakdown: Record<string, number>;
  avgIntervalDays: number;
};

function calculateEntryStats(entries: VehicleEntry[]): EntryStats {
  if (entries.length === 0) {
    return {
      totalEntries: 0,
      totalCost: 0,
      totalKmTraveled: 0,
      firstEntryDate: null,
      lastEntryDate: null,
      minKm: 0,
      maxKm: 0,
      typeBreakdown: {},
      trustLevelBreakdown: {},
      avgIntervalDays: 0,
    };
  }

  const sorted = [...entries].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const firstEntry = sorted[0];
  const lastEntry = sorted[sorted.length - 1];

  const typeBreakdown: Record<string, number> = {};
  const trustLevelBreakdown: Record<string, number> = {};
  let totalCost = 0;
  let minKm = firstEntry.km;
  let maxKm = firstEntry.km;

  for (const entry of entries) {
    typeBreakdown[entry.type] = (typeBreakdown[entry.type] ?? 0) + 1;
    const trustKey = entry.trust_level ?? "keine";
    trustLevelBreakdown[trustKey] = (trustLevelBreakdown[trustKey] ?? 0) + 1;

    if (entry.cost_amount !== null) totalCost += entry.cost_amount;
    minKm = Math.min(minKm, entry.km);
    maxKm = Math.max(maxKm, entry.km);
  }

  const firstDate = new Date(firstEntry.date);
  const lastDate = new Date(lastEntry.date);
  const diffTime = Math.abs(lastDate.getTime() - firstDate.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  const avgIntervalDays = entries.length > 1 ? Math.floor(diffDays / (entries.length - 1)) : 0;

  return {
    totalEntries: entries.length,
    totalCost,
    totalKmTraveled: maxKm - minKm,
    firstEntryDate: firstEntry.date,
    lastEntryDate: lastEntry.date,
    minKm,
    maxKm,
    typeBreakdown,
    trustLevelBreakdown,
    avgIntervalDays,
  };
}

export default function VehicleDetailPage(props: { vehicleId: string }): JSX.Element {
  const vehicleId = props.vehicleId;
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [entries, setEntries] = useState<VehicleEntry[]>([]);
  const [trustSummary, setTrustSummary] = useState<VehicleTrustSummary | null>(null);
  const [historyByEntryId, setHistoryByEntryId] = useState<Record<string, VehicleEntry[]>>({});
  const [entryDraft, setEntryDraft] = useState<EntryDraft>(defaultDraft);
  const [revisionTarget, setRevisionTarget] = useState<VehicleEntry | null>(null);
  const [busy, setBusy] = useState<"entry" | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    const run = async () => {
      setViewState("loading");
      setError("");

      const token = getAuthToken();
      const headers = authHeaders(token);
      const [vehicleRes, entriesRes, trustRes] = await Promise.all([
        getVehicle(vehicleId, { headers }),
        listVehicleEntries(vehicleId, { headers }),
        getVehicleTrustSummary(vehicleId, { headers }),
      ]);
      if (!alive) return;

      if (!vehicleRes.ok) {
        if (vehicleRes.status === 401) {
          handleUnauthorized();
          return;
        }
        if (vehicleRes.status === 403 && toErrorCode(vehicleRes.body) === "forbidden") {
          setViewState("forbidden");
          return;
        }
        setViewState("error");
        setError(toErrorMessage(vehicleRes));
        return;
      }

      if (!entriesRes.ok && entriesRes.status === 401) {
        handleUnauthorized();
        return;
      }
      if (!entriesRes.ok && entriesRes.status !== 404) {
        setViewState("error");
        setError(toErrorMessage(entriesRes));
        return;
      }
      if (!trustRes.ok && trustRes.status === 401) {
        handleUnauthorized();
        return;
      }
      if (!trustRes.ok) {
        setViewState("error");
        setError(toErrorMessage(trustRes));
        return;
      }

      setVehicle(vehicleRes.body);
      setEntries(entriesRes.ok ? entriesRes.body : []);
      setTrustSummary(trustRes.body);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, [vehicleId]);

  const timelineEmpty = entries.length === 0;
  const optionalHint = useMemo(() => "Datenpflege = bessere Trust-Stufe & Verkaufswert", []);
  const entryStats = useMemo(() => calculateEntryStats(entries), [entries]);

  async function refreshEntries(): Promise<void> {
    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await listVehicleEntries(vehicleId, { headers });
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      throw new Error(toErrorMessage(res));
    }
    setEntries(res.body);

    const trustRes = await getVehicleTrustSummary(vehicleId, { headers });
    if (trustRes.ok) {
      setTrustSummary(trustRes.body);
    }
  }

  async function onSubmitEntry() {
    const normalized = normalizeDraft(entryDraft);
    if (!normalized.ok) {
      setError(normalized.error);
      return;
    }

    const token = getAuthToken();
    const headers = authHeaders(token);
    setBusy("entry");
    setError("");

    const res = revisionTarget
      ? await createVehicleEntryRevision(vehicleId, revisionTarget.id, normalized.body, { headers })
      : await createVehicleEntry(vehicleId, normalized.body, { headers });

    setBusy(null);

    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(res));
      return;
    }

    await refreshEntries();
    setEntryDraft(defaultDraft());
    setRevisionTarget(null);
    setHistoryByEntryId((prev) => {
      if (!revisionTarget) return prev;
      const next = { ...prev };
      delete next[revisionTarget.id];
      return next;
    });
  }

  async function loadHistory(entry: VehicleEntry) {
    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await getVehicleEntryHistory(vehicleId, entry.id, { headers });
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(res));
      return;
    }
    setHistoryByEntryId((prev) => ({ ...prev, [entry.id]: res.body }));
  }

  function startRevision(entry: VehicleEntry) {
    setRevisionTarget(entry);
    setEntryDraft({
      date: entry.date,
      type: entry.type,
      performed_by: entry.performed_by,
      km: String(entry.km),
      note: entry.note ?? "",
      cost_amount: entry.cost_amount == null ? "" : String(entry.cost_amount),
      trust_level: entry.trust_level ?? "",
    });
  }

  function cancelRevision() {
    setRevisionTarget(null);
    setEntryDraft(defaultDraft());
  }

  return (
<<<<<<< HEAD
    <main className="ltc-main ltc-main--xl" data-testid="vehicle-detail-page">
      <section className="ltc-page-intro">
        <div className="ltc-page-intro__copy">
          <div className="ltc-page-intro__eyebrow">Vehicle File</div>
          <h1>Vehicle Detail</h1>
          <p>Fahrzeugprofil mit Timeline, Entry-Pflichtfeldern und Versionshistorie.</p>
        </div>
        {vehicle ? (
          <div className="ltc-page-intro__meta">
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Trust-Light</div>
              <div className="ltc-kpi-tile__value">{trustSummary ? trustLightLabel(trustSummary.trust_light) : "..."}</div>
              <div className="ltc-kpi-tile__meta">{vehicle.nickname?.trim() || vehicle.vin_masked}</div>
            </div>
          </div>
        ) : null}
      </section>
=======
    <main className="ltc-main ltc-main--wide">
      <h1>Vehicle Detail</h1>
>>>>>>> origin/main

      {error ? <InlineErrorBanner message={error} /> : null}
      {viewState === "loading" ? <div className="ltc-card">Fahrzeug wird geladen...</div> : null}
      {viewState === "forbidden" ? <ForbiddenPanel /> : null}

      {viewState === "ready" && vehicle ? (
        <>
          <div className="ltc-kpi-band">
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Einträge gesamt</div>
              <div className="ltc-kpi-tile__value">{entryStats.totalEntries}</div>
              <div className="ltc-kpi-tile__meta">Aktive Timeline-Einträge</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Km gefahren</div>
              <div className="ltc-kpi-tile__value">{entryStats.totalKmTraveled.toLocaleString()}</div>
              <div className="ltc-kpi-tile__meta">Zwischen erstem und letztem Eintrag</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Kosten gesamt</div>
              <div className="ltc-kpi-tile__value">{entryStats.totalCost.toFixed(0)} €</div>
              <div className="ltc-kpi-tile__meta">Nur dokumentierte Kosten</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Ø Intervall</div>
              <div className="ltc-kpi-tile__value">{entryStats.avgIntervalDays} Tage</div>
              <div className="ltc-kpi-tile__meta">Zwischen dokumentierten Services</div>
            </div>
          </div>

<<<<<<< HEAD
          <section className="ltc-card ltc-section ltc-section--card ltc-card--subtle">
            <span className="ltc-card__eyebrow">Overview</span>
            <h2>Stammdaten & Kennwerte</h2>
            <div className="ltc-two-col-grid">
              <div>
                <p>
                  <strong>ID:</strong> <code>{vehicle.id}</code>
                </p>
                <p>
                  <strong>VIN:</strong> <code>{vehicle.vin_masked}</code>
                </p>
                <p>
                  <strong>Nickname:</strong> {vehicle.nickname?.trim() || "nicht gesetzt"}
                </p>
              </div>
              <div>
                {entryStats.totalEntries > 0 ? (
                  <>
                    <p>
                      <strong>Erster Eintrag:</strong> {entryStats.firstEntryDate} ({entryStats.minKm.toLocaleString()} km)
                    </p>
                    <p>
                      <strong>Letzter Eintrag:</strong> {entryStats.lastEntryDate} ({entryStats.maxKm.toLocaleString()} km)
                    </p>
                    <p>
                      <strong>Zeitspanne:</strong> ~{Math.floor((new Date(entryStats.lastEntryDate!).getTime() - new Date(entryStats.firstEntryDate!).getTime()) / (1000 * 60 * 60 * 24))} Tage
                    </p>
                  </>
                ) : (
                  <p className="ltc-muted">Noch keine Laufleistungsentwicklung verfügbar.</p>
                )}
              </div>
            </div>

            {Object.keys(entryStats.typeBreakdown).length > 0 && (
              <div className="ltc-section">
                <strong>Eintragstypen</strong>
                <div className="ltc-token-row">
                  {Object.entries(entryStats.typeBreakdown)
                    .sort((a, b) => b[1] - a[1])
                    .map(([type, count]) => (
                      <div key={type} className="ltc-token ltc-token--neutral">
                        <strong>{type}:</strong> {count}x
                      </div>
                    ))}
                </div>
              </div>
            )}

            {Object.keys(entryStats.trustLevelBreakdown).length > 0 && (
              <div className="ltc-section">
                <strong>T-Level Verteilung</strong>
                <div className="ltc-token-row">
                  {Object.entries(entryStats.trustLevelBreakdown).map(([level, count]) => (
                    <div key={level} className="ltc-token ltc-token--warning">
                      <strong>{level === "keine" ? "keine" : level}:</strong> {count}x
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <div className="ltc-layout-grid ltc-layout-grid--sidebar ltc-section" data-testid="vehicle-detail-workspace-grid">
          <div className="ltc-card-stack" data-testid="vehicle-detail-primary">
          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Timeline</span>
=======
          {/* QUICK STATS DASHBOARD */}
          <section className="ltc-card ltc-section ltc-section--card">
            <h3 className="ltc-helper-text">
              📊 Fahrzeug-Übersicht
            </h3>
            <div className="ltc-stats-grid">
              <div className="ltc-stat-card">
                <div className="ltc-stat-card__label">Einträge gesamt</div>
                <div className="ltc-stat-card__value">{entryStats.totalEntries}</div>
              </div>
              <div className="ltc-stat-card">
                <div className="ltc-stat-card__label">Km gefahren</div>
                <div className="ltc-stat-card__value">{entryStats.totalKmTraveled.toLocaleString()}</div>
              </div>
              <div className="ltc-stat-card">
                <div className="ltc-stat-card__label">Kosten gesamt</div>
                <div className="ltc-stat-card__value">{entryStats.totalCost.toFixed(0)} €</div>
              </div>
              <div className="ltc-stat-card">
                <div className="ltc-stat-card__label">Ø Intervall</div>
                <div className="ltc-stat-card__value">{entryStats.avgIntervalDays} Tage</div>
              </div>
            </div>
          </section>

          <section className="ltc-card ltc-section ltc-section--card">
            <h2>Stammdaten & Kennwerte</h2>
            <div className="ltc-two-col-grid">
              <div>
                <p>
                  <strong>ID:</strong> <code>{vehicle.id}</code>
                </p>
                <p>
                  <strong>VIN:</strong> <code>{vehicle.vin_masked}</code>
                </p>
                <p>
                  <strong>Nickname:</strong> {vehicle.nickname?.trim() || "nicht gesetzt"}
                </p>
              </div>
              <div>
                {entryStats.totalEntries > 0 && (
                  <>
                    <p>
                      <strong>Erste Eintrag:</strong> {entryStats.firstEntryDate} ({entryStats.minKm.toLocaleString()} km)
                    </p>
                    <p>
                      <strong>Letzte Eintrag:</strong> {entryStats.lastEntryDate} ({entryStats.maxKm.toLocaleString()} km)
                    </p>
                    <p>
                      <strong>Zeitspanne:</strong> ~{Math.floor((new Date(entryStats.lastEntryDate!).getTime() - new Date(entryStats.firstEntryDate!).getTime()) / (1000 * 60 * 60 * 24))} Tage
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Entry Types Breakdown */}
            {Object.keys(entryStats.typeBreakdown).length > 0 && (
              <div className="ltc-section">
                <strong>Eintragstypen:</strong>
                <div className="ltc-token-row">
                  {Object.entries(entryStats.typeBreakdown)
                    .sort((a, b) => b[1] - a[1])
                    .map(([type, count]) => (
                      <div key={type} className="ltc-token ltc-token--neutral">
                        <strong>{type}:</strong> {count}x
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Trust Levels Breakdown */}
            {Object.keys(entryStats.trustLevelBreakdown).length > 0 && (
              <div className="ltc-section">
                <strong>T-Level Verteilung:</strong>
                <div className="ltc-token-row">
                  {Object.entries(entryStats.trustLevelBreakdown).map(([level, count]) => (
                    <div key={level} className="ltc-token ltc-token--warning">
                      <strong>{level === "keine" ? "keine" : level}:</strong> {count}x
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="ltc-card ltc-section ltc-section--card">
>>>>>>> origin/main
            <h2>Timeline</h2>
            <p className="ltc-muted">
              Pflichtfelder: Datum, Typ, durchgeführt von und Kilometerstand. Optionalfelder bleiben wertsteigernd.
            </p>

            {timelineEmpty ? <p className="ltc-muted">Noch keine Einträge vorhanden.</p> : null}

            {!timelineEmpty ? (
              <ul className="ltc-entry-list">
                {entries.map((entry) => (
                  <li key={entry.id}>
                    <div className="ltc-card ltc-entry-card">
                      <div className="ltc-entry-card__header">
                        <div>
                          <strong>{entry.type}</strong> · <code>{entry.date}</code> · {entry.performed_by}
                        </div>
                        <div className="ltc-muted">
                          {revisionLabel(entry)} · {entry.km} km {entry.trust_level ? `· ${entry.trust_level}` : ""}
                        </div>
                      </div>
                      <p className="ltc-muted ltc-mt-2">
                        {trustLevelMeaning(entry.trust_level)}
                      </p>
                      {entry.note ? <p className="ltc-mt-2">{entry.note}</p> : null}
                      {entry.cost_amount != null ? <p className="ltc-muted">Kosten: {entry.cost_amount.toFixed(2)} EUR</p> : null}

                      <div className="ltc-entry-card__actions">
                        <button type="button" className="ltc-btn ltc-btn--soft" onClick={() => startRevision(entry)}>
                          Neue Version anlegen
                        </button>
                        <button type="button" className="ltc-btn ltc-btn--ghost" onClick={() => void loadHistory(entry)}>
                          Versionshistorie laden
                        </button>
                      </div>

                      {historyByEntryId[entry.id] ? (
                        <div className="ltc-entry-card__history">
                          <strong>Versionen</strong>
                          <ul className="ltc-entry-card__history-list">
                            {historyByEntryId[entry.id].map((version) => (
                              <li key={version.id}>
                                <code>v{version.version}</code> · {version.date} · {version.km} km · {version.performed_by}
                                {!version.is_latest ? " · archiviert" : " · aktuell"}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
          </div>

<<<<<<< HEAD
          <aside className="ltc-card-stack ltc-sticky-desktop" data-testid="vehicle-detail-rail">
          <section className="ltc-card ltc-section ltc-section--card" data-testid="vehicle-detail-trust-card">
            <span className="ltc-card__eyebrow">Trust</span>
            <h2>Trust-Ampel & Bewertung</h2>
            <p className="ltc-muted">T1 = kein physisches Serviceheft, T2 = physisches Serviceheft vorhanden, T3 = Dokument vorhanden.</p>
            {trustSummary ? (
              <div className="ltc-trust-panel">
                <div className="ltc-trust-panel__hero">
                  <div
                    className="ltc-trust-panel__light"
                    style={{ backgroundColor: trustLightColor(trustSummary.trust_light) }}
                    aria-label={`Trust-Light ${trustLightLabel(trustSummary.trust_light)}`}
                  >
=======
          <section className="ltc-card ltc-section ltc-section--card">
            <h2>🚦 Trust-Ampel & Bewertung</h2>
            <p className="ltc-muted">T1 = kein physisches Serviceheft, T2 = physisches Serviceheft vorhanden, T3 = Dokument vorhanden.</p>
            {trustSummary ? (
              <div className="ltc-trust-panel">
                {/* Visual Trust Light Indicator */}
                <div className="ltc-trust-panel__hero">
                  <div className="ltc-trust-panel__light" style={{
                     width: 60,
                     height: 60,
                     backgroundColor: trustLightColor(trustSummary.trust_light),
                     boxShadow: `0 4px 6px rgba(0, 0, 0, 0.1)`
                   }}>
>>>>>>> origin/main
                     {trustSummary.trust_light === "gruen" ? "✓" : trustSummary.trust_light === "gelb" ? "⚠" : "!"}
                  </div>
                  <div>
                    <div className="ltc-trust-panel__hero-value">
                      {trustLightLabel(trustSummary.trust_light)}
                    </div>
                    <div className="ltc-trust-panel__hero-meta">
                      Verifikation: <strong>{trustSummary.verification_level}</strong>
                    </div>
                    <div className="ltc-trust-panel__hero-meta">
                      Oberstes T-Level: <strong>{trustSummary.top_trust_level ?? "–"}</strong>
                    </div>
                  </div>
                </div>

<<<<<<< HEAD
=======
                {/* Status Grid */}
>>>>>>> origin/main
                <div className="ltc-status-grid">
                  <div className={`ltc-status-card ${trustSummary.history_status === "vorhanden" ? "ltc-status-card--success" : "ltc-status-card--error"}`}>
                    <div><strong>Historie</strong></div>
                    <div className="ltc-muted">
                      {trustSummary.history_status === "vorhanden" ? "✓ Vorhanden" : "✗ Keine"}
                    </div>
                  </div>
                  <div className={`ltc-status-card ${trustSummary.evidence_status === "vorhanden" ? "ltc-status-card--success" : "ltc-status-card--error"}`}>
                    <div><strong>Nachweise</strong></div>
                    <div className="ltc-muted">
                      {trustSummary.evidence_status === "vorhanden" ? "✓ Vorhanden" : "✗ Keine"}
                    </div>
                  </div>
                  <div className={`ltc-status-card ${trustSummary.accident_status === "unfallfrei" ? "ltc-status-card--success" : trustSummary.accident_status === "nicht_unfallfrei" ? "ltc-status-card--error" : "ltc-status-card--neutral"}`}>
                    <div><strong>Unfallstatus</strong></div>
                    <div className="ltc-muted">
                      {trustSummary.accident_status_label}
                    </div>
                  </div>
                </div>

<<<<<<< HEAD
                <p className="ltc-inline-note ltc-inline-note--info">
                  {trustSummary.hint}
                </p>

                {trustSummary.reason_codes.length > 0 ? (
                  <div>
                    <strong className="ltc-helper-text">Bewertungsfaktoren</strong>
=======
                {/* Hint */}
                <p className="ltc-inline-note ltc-inline-note--info">
                  💡 {trustSummary.hint}
                </p>

                {/* Reason Codes */}
                {trustSummary.reason_codes.length > 0 ? (
                  <div>
                    <strong className="ltc-helper-text">
                      Bewertungsfaktoren
                    </strong>
>>>>>>> origin/main
                    <div className="ltc-token-row">
                      {trustSummary.reason_codes.map((code) => (
                        <div key={code} className="ltc-token ltc-token--neutral">
                          {code}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

<<<<<<< HEAD
                {trustSummary.todo_codes.length > 0 ? (
                  <div className="ltc-inline-note ltc-inline-note--warning">
                    <strong className="ltc-helper-text">Priorisierte To-dos</strong>
=======
                {/* To-Do Codes */}
                {trustSummary.todo_codes.length > 0 ? (
                  <div className="ltc-inline-note ltc-inline-note--warning">
                    <strong className="ltc-helper-text">
                      Priorisierte To-dos
                    </strong>
>>>>>>> origin/main
                    <div className="ltc-token-row">
                      {trustSummary.todo_codes.map((code) => (
                        <div key={code} className="ltc-token ltc-token--warning">
                          {code}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="ltc-muted">Trust-Zusammenfassung wird geladen…</p>
            )}
          </section>
<<<<<<< HEAD
          <section className="ltc-card ltc-section ltc-section--card ltc-card--subtle">
            <span className="ltc-card__eyebrow">Entry Editor</span>
=======

          <section className="ltc-card ltc-section ltc-section--card">
>>>>>>> origin/main
            <h2>{revisionTarget ? "Entry-Version aktualisieren" : "Neuen Entry anlegen"}</h2>
            <p className="ltc-muted">{optionalHint}</p>
            <p className="ltc-muted">T1/T2/T3 bitte nur entsprechend der Nachweislage setzen.</p>

            {revisionTarget ? (
              <p className="ltc-muted">
                Neue Version für <code>{revisionTarget.id}</code> · aktuell {revisionLabel(revisionTarget)}
              </p>
            ) : null}

            <div className="ltc-stack">
              <label>
                Datum
                <input
                  type="date"
                  value={entryDraft.date}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, date: e.target.value }))}
                  className="ltc-form-group__input"
                />
              </label>
              <label>
                Typ
                <input
                  type="text"
                  value={entryDraft.type}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, type: e.target.value }))}
                  className="ltc-form-group__input"
                />
              </label>
              <label>
                Durchgeführt von
                <input
                  type="text"
                  value={entryDraft.performed_by}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, performed_by: e.target.value }))}
                  className="ltc-form-group__input"
                />
              </label>
              <label>
                Kilometerstand
                <input
                  type="number"
                  min={0}
                  value={entryDraft.km}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, km: e.target.value }))}
                  className="ltc-form-group__input"
                />
              </label>
              <label>
                Bemerkung (optional)
                <textarea
                  value={entryDraft.note}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, note: e.target.value }))}
                  className="ltc-form-group__textarea"
                />
              </label>
              <label>
                Kostenbetrag in EUR (optional)
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={entryDraft.cost_amount}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, cost_amount: e.target.value }))}
                  className="ltc-form-group__input"
                />
              </label>
              <label>
                T-Status (optional)
                <select
                  value={entryDraft.trust_level}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, trust_level: e.target.value as EntryDraft["trust_level"] }))}
                  className="ltc-form-group__select"
                >
                  <option value="">Nicht gesetzt</option>
                  <option value="T1">T1</option>
                  <option value="T2">T2</option>
                  <option value="T3">T3</option>
                </select>
              </label>
            </div>

            <div className="ltc-entry-card__actions">
              <button type="button" className="ltc-btn ltc-btn--primary" disabled={busy === "entry"} onClick={() => void onSubmitEntry()}>
                {busy === "entry" ? "Speichert..." : revisionTarget ? "Version speichern" : "Entry speichern"}
              </button>
              {revisionTarget ? (
                <button type="button" className="ltc-btn ltc-btn--ghost" disabled={busy === "entry"} onClick={cancelRevision}>
                  Revision abbrechen
                </button>
              ) : null}
            </div>
          </section>

          <section className="ltc-card ltc-section ltc-section--card">
<<<<<<< HEAD
            <span className="ltc-card__eyebrow">Module</span>
=======
>>>>>>> origin/main
            <h2>Trust-Modul</h2>
            <p>
              Für dieses Fahrzeug können Trust-Folders add-on-gated und consent-gated geöffnet werden. Der Link übergibt den
              Vehicle-Kontext direkt in die Trust-Folder-Ansicht.
            </p>
            <a href={trustFoldersHref(vehicle.id)}>Trust Folders für dieses Vehicle öffnen</a>
          </section>
          </aside>
          </div>

          <section className="ltc-page-nav">
            <h2>Navigation</h2>
            <ul className="ltc-list">
              <li className="ltc-list__item">
                <a className="ltc-list__link" href="#/vehicles">Zurück zur Vehicles-Liste</a>
              </li>
              <li className="ltc-list__item">
                <a className="ltc-list__link" href="#/documents">Zu Documents</a>
              </li>
              <li className="ltc-list__item">
                <a className="ltc-list__link" href={trustFoldersHref(vehicle.id)}>Zu Trust Folders</a>
              </li>
            </ul>
          </section>
        </>
      ) : null}
    </main>
  );
}
