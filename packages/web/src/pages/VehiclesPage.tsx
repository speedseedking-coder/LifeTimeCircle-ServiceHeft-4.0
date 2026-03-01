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
  const [errorField, setErrorField] = useState<"vin" | null>(null);
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
      setErrorField("vin");
      return;
    }

    setCreating(true);
    setError("");
    setErrorField(null);

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
      setErrorField(null);
      return;
    }

    setVehicles((prev) => [...prev, res.body]);
    setVin("");
    setNickname("");
    setAccidentStatus("unknown");
    window.location.hash = `#/vehicles/${encodeURIComponent(res.body.id)}`;
  }

  return (
<<<<<<< HEAD
    <main className="ltc-main ltc-main--xl" data-testid="vehicles-page">
      <section className="ltc-page-intro">
        <div className="ltc-page-intro__copy">
          <div className="ltc-page-intro__eyebrow">Owner Workspace</div>
          <h1>Vehicles</h1>
          <p>Owner-scoped Vehicle-Liste mit serverseitigem Consent-, RBAC- und Object-Level-Enforcement.</p>
        </div>
        <div className="ltc-page-intro__meta">
          <div className="ltc-kpi-tile">
            <div className="ltc-kpi-tile__label">Fahrzeuge</div>
            <div className="ltc-kpi-tile__value">{vehicles.length}</div>
            <div className="ltc-kpi-tile__meta">Aktuell im sichtbaren Owner-Workspace.</div>
          </div>
        </div>
=======
    <main className="ltc-main ltc-main--wide">
      <h1>Vehicles</h1>
      <p>Owner-scoped Vehicle-Liste mit serverseitigem Consent-, RBAC- und Object-Level-Enforcement.</p>

      <section className="ltc-card ltc-section--card">
        <h2>Neues Fahrzeug anlegen</h2>
        <form onSubmit={(e) => void onCreate(e)}>
          <div className="ltc-form-grid">
            <div className="ltc-form-group">
              <label className="ltc-form-group__label">
                VIN
                <input
                  className="ltc-form-group__input"
                  value={vin}
                  onChange={(e) => setVin(e.target.value)}
                  placeholder="z. B. WAUZZZ..."
                  autoComplete="off"
                />
              </label>
            </div>
            <div className="ltc-form-group">
              <label className="ltc-form-group__label">
                Nickname (optional)
                <input
                  className="ltc-form-group__input"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="z. B. Familienauto"
                  autoComplete="off"
                />
              </label>
            </div>
            <div className="ltc-form-group">
              <label className="ltc-form-group__label">
                Unfallstatus
                <select
                  className="ltc-form-group__select"
                  value={accidentStatus}
                  onChange={(e) => setAccidentStatus(e.target.value as typeof accidentStatus)}
                >
                  <option value="unknown">Unbekannt</option>
                  <option value="accident_free">Unfallfrei</option>
                  <option value="not_free">Nicht unfallfrei</option>
                </select>
              </label>
            </div>
          </div>

          <div className="ltc-button-group">
            <button type="submit" className="ltc-button ltc-button--primary" disabled={creating}>
              {creating ? "Speichert..." : "Fahrzeug speichern"}
            </button>
          </div>
        </form>
>>>>>>> origin/main
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}

<<<<<<< HEAD
      <div className="ltc-layout-grid ltc-layout-grid--sidebar ltc-section" data-testid="vehicles-desktop-grid">
        <div className="ltc-card-stack">
          <section className="ltc-card ltc-section--card ltc-card--subtle">
            <span className="ltc-card__eyebrow">Create</span>
            <h2>Neues Fahrzeug anlegen</h2>
            <form onSubmit={(e) => void onCreate(e)}>
              <div className="ltc-form-grid ltc-form-grid--wide">
                <div className="ltc-form-group">
                  <label className="ltc-form-group__label" htmlFor="vehicles-vin-input">
                    VIN
                    <input
                      id="vehicles-vin-input"
                      className="ltc-form-group__input"
                      value={vin}
                      onChange={(e) => setVin(e.target.value)}
                      placeholder="z. B. WAUZZZ..."
                      autoComplete="off"
                      aria-required="true"
                      aria-invalid={errorField === "vin"}
                      aria-describedby={errorField === "vin" ? "vehicles-vin-error vehicles-vin-hint" : "vehicles-vin-hint"}
                    />
                  </label>
                  <p id="vehicles-vin-hint" className="ltc-helper-text">
                    11 bis 17 Zeichen, ohne I, O und Q.
                  </p>
                  {errorField === "vin" && error ? (
                    <p id="vehicles-vin-error" className="ltc-helper-text ltc-helper-text--error">
                      {error}
                    </p>
                  ) : null}
                </div>
                <div className="ltc-form-group">
                  <label className="ltc-form-group__label" htmlFor="vehicles-nickname-input">
                    Nickname (optional)
                    <input
                      id="vehicles-nickname-input"
                      className="ltc-form-group__input"
                      value={nickname}
                      onChange={(e) => setNickname(e.target.value)}
                      placeholder="z. B. Familienauto"
                      autoComplete="off"
                    />
                  </label>
                </div>
                <div className="ltc-form-group ltc-form-grid__span-2">
                  <label className="ltc-form-group__label" htmlFor="vehicles-accident-status">
                    Unfallstatus
                    <select
                      id="vehicles-accident-status"
                      className="ltc-form-group__select"
                      value={accidentStatus}
                      onChange={(e) => setAccidentStatus(e.target.value as typeof accidentStatus)}
                      aria-required="true"
                    >
                      <option value="unknown">Unbekannt</option>
                      <option value="accident_free">Unfallfrei</option>
                      <option value="not_free">Nicht unfallfrei</option>
                    </select>
                  </label>
                </div>
              </div>

              <div className="ltc-button-group">
                <button type="submit" className="ltc-button ltc-button--primary" disabled={creating}>
                  {creating ? "Speichert..." : "Fahrzeug speichern"}
                </button>
              </div>
            </form>
          </section>

          <section className="ltc-page-nav">
            <h2>Navigation (Hash)</h2>
            <ul className="ltc-list">
              <li className="ltc-list__item">
                <a className="ltc-list__link" href="#/documents">Zu Documents</a>
              </li>
              <li className="ltc-list__item">
                <a className="ltc-list__link" href="#/onboarding">Zu Onboarding</a>
              </li>
              <li className="ltc-list__item">
                <a className="ltc-list__link" href="#/consent">Zu Consent</a>
              </li>
=======
      {viewState === "loading" ? (
        <section className="ltc-card ltc-section--card">
          <div className="ltc-muted">Vehicles werden geladen...</div>
        </section>
      ) : null}

      {viewState === "ready" ? (
        <section className="ltc-card ltc-section--card">
          <h2>Meine Fahrzeuge</h2>
          {vehicles.length === 0 ? (
            <p className="ltc-muted">Noch keine Fahrzeuge vorhanden.</p>
          ) : (
            <ul className="ltc-list">
              {vehicles.map((vehicle) => (
                <li key={vehicle.id} className="ltc-list__item">
                  <a className="ltc-list__link" href={`#/vehicles/${encodeURIComponent(vehicle.id)}`}>
                    {vehicle.nickname?.trim() || vehicle.vin_masked}
                  </a>{" "}
                  <span className="ltc-muted">({vehicle.vin_masked})</span> ·{" "}
                  <a className="ltc-list__link" href={trustFoldersHref(vehicle.id)}>
                    Trust Folders
                  </a>
                </li>
              ))}
>>>>>>> origin/main
            </ul>
          </section>
        </div>

<<<<<<< HEAD
        <aside className="ltc-card-stack">
          <section className="ltc-card ltc-section--card" data-testid="vehicles-list-card">
            <span className="ltc-card__eyebrow">Fleet</span>
            <h2>Meine Fahrzeuge</h2>
            {viewState === "loading" ? <div className="ltc-muted">Vehicles werden geladen...</div> : null}
            {viewState === "ready" && vehicles.length === 0 ? <p className="ltc-muted">Noch keine Fahrzeuge vorhanden.</p> : null}
            {viewState === "ready" && vehicles.length > 0 ? (
              <ul className="ltc-list">
                {vehicles.map((vehicle) => (
                  <li key={vehicle.id} className="ltc-list__item">
                    <a className="ltc-list__link" href={`#/vehicles/${encodeURIComponent(vehicle.id)}`}>
                      {vehicle.nickname?.trim() || vehicle.vin_masked}
                    </a>{" "}
                    <span className="ltc-muted">({vehicle.vin_masked})</span> ·{" "}
                    <a className="ltc-list__link" href={trustFoldersHref(vehicle.id)}>
                      Trust Folders
                    </a>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>

          <section className="ltc-card ltc-section--card">
            <span className="ltc-card__eyebrow">Hinweis</span>
            <h2>Arbeitskontext</h2>
            <p className="ltc-muted">
              Neue Fahrzeuge landen direkt in der Owner-Ansicht. Der nächste sinnvolle Schritt ist danach die Detailpflege mit Timeline,
              Trust-Folders und Nachweisen.
            </p>
          </section>
        </aside>
      </div>
=======
      <section className="ltc-page-nav">
        <h2>Navigation (Hash)</h2>
        <ul className="ltc-list">
          <li className="ltc-list__item">
            <a className="ltc-list__link" href="#/documents">Zu Documents</a>
          </li>
          <li className="ltc-list__item">
            <a className="ltc-list__link" href="#/onboarding">Zu Onboarding</a>
          </li>
          <li className="ltc-list__item">
            <a className="ltc-list__link" href="#/consent">Zu Consent</a>
          </li>
        </ul>
      </section>
>>>>>>> origin/main
    </main>
  );
}
