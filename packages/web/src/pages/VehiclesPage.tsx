import { FormEvent, useEffect, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { authHeaders, getAuthToken } from "../lib.auth";
import { createVehicle, listVehicles, type Vehicle } from "../vehiclesApi";
import { handleUnauthorized } from "../lib/handleUnauthorized";

type ViewState = "loading" | "ready" | "error";

const VIN_PATTERN = /^[A-HJ-NPR-Z0-9]{11,17}$/;

function trustFoldersHref(vehicleId: string): string {
  return `#/trust-folders?vehicle_id=${encodeURIComponent(vehicleId)}&addon_key=restauration`;
}

function toErrorMessage(result: { status: number; body?: unknown; error: string }): string {
  const body = result.body;
  let code = "";
  if (typeof body === "string") code = body;
  else if (body && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") code = detail;
    else if (detail && typeof detail === "object" && typeof (detail as { code?: unknown }).code === "string") {
      code = (detail as { code: string }).code;
    }
  }

  if (result.status === 403 && code === "vehicle_limit_reached") {
    return "Fahrzeuglimit erreicht. Für Standard-User ist serverseitig nur 1 Fahrzeug kostenfrei erlaubt.";
  }
  if (result.status === 422 && code === "invalid_vin_format") {
    return "Die VIN ist ungültig. Erlaubt sind 11 bis 17 Zeichen ohne I, O und Q.";
  }
  if (result.status === 404 && code === "not_found") {
    return "Fahrzeug nicht gefunden.";
  }
  if (result.status === 403 && code === "consent_required") {
    window.location.hash = "#/consent";
    return "Consent erforderlich.";
  }
  return "Vehicles konnten nicht verarbeitet werden.";
}

export default function VehiclesPage(): JSX.Element {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState("");
  const [vin, setVin] = useState("");
  const [nickname, setNickname] = useState("");
  const [accidentStatus, setAccidentStatus] = useState<"unknown" | "accident_free" | "not_free">("unknown");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let alive = true;

    const run = async () => {
      setViewState("loading");
      setError("");

      const token = getAuthToken();
      const headers = authHeaders(token);
      const res = await listVehicles({ headers });
      if (!alive) return;

      if (!res.ok) {
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        setViewState("error");
        setError(toErrorMessage(res));
        return;
      }

      setVehicles(res.body);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const normalizedVin = vin.trim().toUpperCase().replace(/\s+/g, "");
    if (!VIN_PATTERN.test(normalizedVin)) {
      setError("Die VIN muss 11 bis 17 Zeichen haben und darf I, O, Q nicht enthalten.");
      return;
    }

    setCreating(true);
    setError("");

    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await createVehicle(
      {
        vin: normalizedVin,
        nickname,
        meta: { accident_status: accidentStatus },
      },
      { headers },
    );

    setCreating(false);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(res));
      return;
    }

    setVehicles((prev) => [...prev, res.body]);
    setVin("");
    setNickname("");
    setAccidentStatus("unknown");
    window.location.hash = `#/vehicles/${encodeURIComponent(res.body.id)}`;
  }

  return (
    <main style={{ padding: 12 }}>
      <h1>Vehicles</h1>
      <p>Owner-scoped Vehicle-Liste mit serverseitigem Consent-, RBAC- und Object-Level-Enforcement.</p>

      <section className="ltc-card" style={{ marginTop: 16 }}>
        <h2>Neues Fahrzeug anlegen</h2>
        <form onSubmit={(e) => void onCreate(e)}>
          <div style={{ display: "grid", gap: 10, maxWidth: 420 }}>
            <label>
              VIN
              <input
                value={vin}
                onChange={(e) => setVin(e.target.value)}
                placeholder="z. B. WAUZZZ..."
                autoComplete="off"
                style={{ display: "block", marginTop: 8, padding: 10, width: "100%" }}
              />
            </label>
            <label>
              Nickname (optional)
              <input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="z. B. Familienauto"
                autoComplete="off"
                style={{ display: "block", marginTop: 8, padding: 10, width: "100%" }}
              />
            </label>
            <label>
              Unfallstatus
              <select
                value={accidentStatus}
                onChange={(e) => setAccidentStatus(e.target.value as typeof accidentStatus)}
                style={{ display: "block", marginTop: 8, padding: 10, width: "100%" }}
              >
                <option value="unknown">Unbekannt</option>
                <option value="accident_free">Unfallfrei</option>
                <option value="not_free">Nicht unfallfrei</option>
              </select>
            </label>
          </div>

          <button type="submit" disabled={creating} style={{ marginTop: 12, padding: "10px 14px" }}>
            {creating ? "Speichert..." : "Fahrzeug speichern"}
          </button>
        </form>
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}

      {viewState === "loading" ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <div className="ltc-muted">Vehicles werden geladen...</div>
        </section>
      ) : null}

      {viewState === "ready" ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <h2>Meine Fahrzeuge</h2>
          {vehicles.length === 0 ? (
            <p className="ltc-muted">Noch keine Fahrzeuge vorhanden.</p>
          ) : (
            <ul>
              {vehicles.map((vehicle) => (
                <li key={vehicle.id}>
                  <a href={`#/vehicles/${encodeURIComponent(vehicle.id)}`}>
                    {vehicle.nickname?.trim() || vehicle.vin_masked}
                  </a>{" "}
                  <span className="ltc-muted">({vehicle.vin_masked})</span> ·{" "}
                  <a href={trustFoldersHref(vehicle.id)}>Trust Folders</a>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href="#/documents">Zu Documents</a>
          </li>
          <li>
            <a href="#/onboarding">Zu Onboarding</a>
          </li>
          <li>
            <a href="#/consent">Zu Consent</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
