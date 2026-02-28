import { useEffect, useMemo, useState } from "react";
import ForbiddenPanel from "../components/ForbiddenPanel";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";
import {
  createVehicleEntry,
  createVehicleEntryRevision,
  getVehicle,
  getVehicleEntryHistory,
  listVehicleEntries,
  type Vehicle,
  type VehicleEntry,
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

export default function VehicleDetailPage(props: { vehicleId: string }): JSX.Element {
  const vehicleId = props.vehicleId;
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [entries, setEntries] = useState<VehicleEntry[]>([]);
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
      const [vehicleRes, entriesRes] = await Promise.all([
        getVehicle(vehicleId, { headers }),
        listVehicleEntries(vehicleId, { headers }),
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

      setVehicle(vehicleRes.body);
      setEntries(entriesRes.ok ? entriesRes.body : []);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, [vehicleId]);

  const timelineEmpty = entries.length === 0;
  const optionalHint = useMemo(() => "Datenpflege = bessere Trust-Stufe & Verkaufswert", []);

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
    <main style={{ padding: 24, maxWidth: 980, margin: "0 auto" }}>
      <h1>Vehicle Detail</h1>

      {error ? <InlineErrorBanner message={error} /> : null}
      {viewState === "loading" ? <div className="ltc-card">Fahrzeug wird geladen...</div> : null}
      {viewState === "forbidden" ? <ForbiddenPanel /> : null}

      {viewState === "ready" && vehicle ? (
        <>
          <p>Fahrzeugprofil mit Timeline, Entry-Pflichtfeldern und Versionshistorie.</p>

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <h2>Stammdaten</h2>
            <p>
              <strong>ID:</strong> <code>{vehicle.id}</code>
            </p>
            <p>
              <strong>VIN:</strong> <code>{vehicle.vin_masked}</code>
            </p>
            <p>
              <strong>Nickname:</strong> {vehicle.nickname?.trim() || "nicht gesetzt"}
            </p>
          </section>

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <h2>Timeline</h2>
            <p className="ltc-muted">
              Pflichtfelder: Datum, Typ, durchgeführt von und Kilometerstand. Optionalfelder bleiben wertsteigernd.
            </p>

            {timelineEmpty ? <p className="ltc-muted">Noch keine Einträge vorhanden.</p> : null}

            {!timelineEmpty ? (
              <ul style={{ display: "grid", gap: 12, paddingLeft: 18 }}>
                {entries.map((entry) => (
                  <li key={entry.id}>
                    <div className="ltc-card">
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                        <div>
                          <strong>{entry.type}</strong> · <code>{entry.date}</code> · {entry.performed_by}
                        </div>
                        <div className="ltc-muted">
                          {revisionLabel(entry)} · {entry.km} km {entry.trust_level ? `· ${entry.trust_level}` : ""}
                        </div>
                      </div>
                      {entry.note ? <p style={{ marginTop: 10 }}>{entry.note}</p> : null}
                      {entry.cost_amount != null ? <p className="ltc-muted">Kosten: {entry.cost_amount.toFixed(2)} EUR</p> : null}

                      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
                        <button type="button" onClick={() => startRevision(entry)}>
                          Neue Version anlegen
                        </button>
                        <button type="button" onClick={() => void loadHistory(entry)}>
                          Versionshistorie laden
                        </button>
                      </div>

                      {historyByEntryId[entry.id] ? (
                        <div style={{ marginTop: 12 }}>
                          <strong>Versionen</strong>
                          <ul style={{ marginTop: 8 }}>
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

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <h2>{revisionTarget ? "Entry-Version aktualisieren" : "Neuen Entry anlegen"}</h2>
            <p className="ltc-muted">{optionalHint}</p>

            {revisionTarget ? (
              <p className="ltc-muted">
                Neue Version für <code>{revisionTarget.id}</code> · aktuell {revisionLabel(revisionTarget)}
              </p>
            ) : null}

            <div style={{ display: "grid", gap: 10, maxWidth: 520 }}>
              <label>
                Datum
                <input
                  type="date"
                  value={entryDraft.date}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, date: e.target.value }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>
              <label>
                Typ
                <input
                  type="text"
                  value={entryDraft.type}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, type: e.target.value }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>
              <label>
                Durchgeführt von
                <input
                  type="text"
                  value={entryDraft.performed_by}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, performed_by: e.target.value }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>
              <label>
                Kilometerstand
                <input
                  type="number"
                  min={0}
                  value={entryDraft.km}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, km: e.target.value }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>
              <label>
                Bemerkung (optional)
                <textarea
                  value={entryDraft.note}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, note: e.target.value }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10, minHeight: 96 }}
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
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>
              <label>
                T-Status (optional)
                <select
                  value={entryDraft.trust_level}
                  onChange={(e) => setEntryDraft((prev) => ({ ...prev, trust_level: e.target.value as EntryDraft["trust_level"] }))}
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                >
                  <option value="">Nicht gesetzt</option>
                  <option value="T1">T1</option>
                  <option value="T2">T2</option>
                  <option value="T3">T3</option>
                </select>
              </label>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
              <button type="button" disabled={busy === "entry"} onClick={() => void onSubmitEntry()}>
                {busy === "entry" ? "Speichert..." : revisionTarget ? "Version speichern" : "Entry speichern"}
              </button>
              {revisionTarget ? (
                <button type="button" disabled={busy === "entry"} onClick={cancelRevision}>
                  Revision abbrechen
                </button>
              ) : null}
            </div>
          </section>

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <h2>Trust-Modul</h2>
            <p>
              Für dieses Fahrzeug können Trust-Folders add-on-gated und consent-gated geöffnet werden. Der Link übergibt den
              Vehicle-Kontext direkt in die Trust-Folder-Ansicht.
            </p>
            <a href={trustFoldersHref(vehicle.id)}>Trust Folders für dieses Vehicle öffnen</a>
          </section>

          <section style={{ marginTop: 16 }}>
            <h2>Navigation</h2>
            <ul>
              <li>
                <a href="#/vehicles">Zurück zur Vehicles-Liste</a>
              </li>
              <li>
                <a href="#/documents">Zu Documents</a>
              </li>
              <li>
                <a href={trustFoldersHref(vehicle.id)}>Zu Trust Folders</a>
              </li>
            </ul>
          </section>
        </>
      ) : null}
    </main>
  );
}
