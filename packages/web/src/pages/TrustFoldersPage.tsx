import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { authHeaders, getAuthToken } from "../lib.auth";
import { createTrustFolder, listTrustFolders, TrustFolder } from "../trustFoldersApi";
import ForbiddenPanel from "../components/ForbiddenPanel";
import AddonRequiredPanel from "../components/AddonRequiredPanel";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { useHash } from "../hooks/useHash";
import { readTrustFolderContextFromHash } from "../lib/trustFolderContext";
import { handleApiNotOk } from "../lib/handleApiGates";

type ViewState = "loading" | "ready" | "forbidden" | "addon" | "error";
const MAX_NAME_LENGTH = 80;

export default function TrustFoldersPage(): JSX.Element {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [items, setItems] = useState<TrustFolder[]>([]);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  const hash = useHash();
  const context = useMemo(() => readTrustFolderContextFromHash(hash), [hash]);

  const load = useCallback(async (vehicleId: string, addonKey: string) => {
    setViewState("loading");
    setError("");

    const token = getAuthToken();
    const headers = authHeaders(token);

    const res = await listTrustFolders(vehicleId, addonKey, { headers });
    if (!res.ok) {
      handleApiNotOk(res, { setViewState, setError, fallbackError: "Trust-Folders konnten nicht geladen werden." });
      return;
    }

    setItems(res.body);
    setViewState("ready");
  }, []);

  useEffect(() => {
    if (!context.vehicleId) return;
    void load(context.vehicleId, context.addonKey);
  }, [context.vehicleId, context.addonKey, load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError("");

    if (!context.vehicleId) {
      setError("Vehicle-Kontext fehlt.");
      return;
    }

    const nextTitle = name.trim();
    if (nextTitle.length < 1) {
      setError("Name darf nicht leer sein.");
      return;
    }
    if (nextTitle.length > MAX_NAME_LENGTH) {
      setError(`Name darf maximal ${MAX_NAME_LENGTH} Zeichen enthalten.`);
      return;
    }

    setCreating(true);
    const token = getAuthToken();
    const headers = authHeaders(token);

    const res = await createTrustFolder(context.vehicleId, nextTitle, context.addonKey, { headers });
    setCreating(false);

    if (!res.ok) {
      handleApiNotOk(res, { setViewState, setError, fallbackError: "Trust-Folder konnte nicht erstellt werden." });
      return;
    }

    setName("");
    await load(context.vehicleId, context.addonKey);
  }

  if (!context.vehicleId) {
    return (
      <main style={{ padding: 12 }}>
        <h1>Trust Folders</h1>
        <div className="ltc-card" role="status" style={{ marginTop: 12 }}>
          <div className="ltc-card__title">Bitte Vehicle wählen</div>
          <div className="ltc-muted">Öffne zuerst ein Fahrzeug und starte Trust-Folders mit Vehicle-Kontext.</div>
          <div style={{ marginTop: 10 }}>
            <a className="ltc-link" href="#/vehicles">
              Zu Vehicles
            </a>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main style={{ padding: 12 }}>
      <h1>Trust Folders</h1>
      <p>
        Vehicle: <code>{context.vehicleId}</code> · Add-on: <code>{context.addonKey}</code>
      </p>

      <section className="ltc-card" style={{ marginTop: 12 }}>
        <form onSubmit={(e) => void onCreate(e)}>
          <label htmlFor="trust-folder-title">Neuer Folder Name</label>
          <input
            id="trust-folder-title"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={MAX_NAME_LENGTH}
            style={{ width: "100%", marginTop: 8, padding: 10 }}
          />
          <button type="submit" disabled={creating} style={{ marginTop: 10, padding: "8px 12px" }}>
            {creating ? "Erstelle…" : "Folder erstellen"}
          </button>
        </form>
      </section>

      {error && <InlineErrorBanner message={error} />}
      {viewState === "loading" && <div className="ltc-card">Lädt…</div>}
      {viewState === "forbidden" && <ForbiddenPanel />}
      {viewState === "addon" && <AddonRequiredPanel />}
      {viewState === "error" && !error && <InlineErrorBanner message="Unerwarteter Fehler." />}

      {viewState === "ready" && (
        <section className="ltc-card" style={{ marginTop: 12 }}>
          <h2>Liste</h2>
          {items.length === 0 ? (
            <p className="ltc-muted">Noch keine Trust-Folders vorhanden.</p>
          ) : (
            <ul>
              {items.map((folder) => (
                <li key={folder.id}>
                  <a
                    href={`#/trust-folders/${folder.id}?vehicle_id=${encodeURIComponent(
                      context.vehicleId,
                    )}&addon_key=${encodeURIComponent(context.addonKey)}`}
                  >
                    {folder.title}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}