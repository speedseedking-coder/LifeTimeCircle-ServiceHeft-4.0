import { useEffect, useState } from "react";
import ForbiddenPanel from "../components/ForbiddenPanel";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";
import { getVehicle, type Vehicle } from "../vehiclesApi";

type ViewState = "loading" | "ready" | "forbidden" | "error";

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

  if (result.status === 404 && code === "not_found") return "Fahrzeug wurde nicht gefunden.";
  if (result.status === 403 && code === "consent_required") {
    window.location.hash = "#/consent";
    return "Consent erforderlich.";
  }
  return "Fahrzeugdetail konnte nicht geladen werden.";
}

export default function VehicleDetailPage(props: { vehicleId: string }): JSX.Element {
  const vehicleId = props.vehicleId;
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    const run = async () => {
      setViewState("loading");
      setError("");

      const token = getAuthToken();
      const headers = authHeaders(token);
      const res = await getVehicle(vehicleId, { headers });
      if (!alive) return;

      if (!res.ok) {
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        if (res.status === 403 && res.body && JSON.stringify(res.body).toLowerCase().includes("forbidden")) {
          setViewState("forbidden");
          return;
        }
        setViewState("error");
        setError(toErrorMessage(res));
        return;
      }

      setVehicle(res.body);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, [vehicleId]);

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>Vehicle Detail</h1>

      {error ? <InlineErrorBanner message={error} /> : null}
      {viewState === "loading" ? <div className="ltc-card">Fahrzeug wird geladen...</div> : null}
      {viewState === "forbidden" ? <ForbiddenPanel /> : null}

      {viewState === "ready" && vehicle ? (
        <>
          <p>Detailansicht zu einem Fahrzeug mit Einstieg in nachgelagerte Produktbereiche.</p>

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
