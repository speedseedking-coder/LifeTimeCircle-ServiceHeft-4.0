import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  const [errorField, setErrorField] = useState<"name" | null>(null);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const nameInputRef = useRef<HTMLInputElement | null>(null);

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

  useEffect(() => {
    if (viewState === "ready") {
      nameInputRef.current?.focus();
    }
  }, [viewState, items.length]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError("");
    setErrorField(null);

    if (!context.vehicleId) {
      setError("Vehicle-Kontext fehlt.");
      return;
    }

    const nextTitle = name.trim();
    if (nextTitle.length < 1) {
      setError("Name darf nicht leer sein.");
      setErrorField("name");
      nameInputRef.current?.focus();
      return;
    }
    if (nextTitle.length > MAX_NAME_LENGTH) {
      setError(`Name darf maximal ${MAX_NAME_LENGTH} Zeichen enthalten.`);
      setErrorField("name");
      nameInputRef.current?.focus();
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
      <main className="ltc-main ltc-main--narrow">
        <h1>Trust Folders</h1>
        <div className="ltc-card ltc-section" role="status">
          <div className="ltc-card__title">Bitte Vehicle wählen</div>
          <div className="ltc-muted">Öffne zuerst ein Fahrzeug und starte Trust-Folders mit Vehicle-Kontext.</div>
          <div className="ltc-mt-4">
            <a className="ltc-link" href="#/vehicles">
              Zu Vehicles
            </a>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="ltc-main ltc-main--narrow" data-testid="trust-folders-page">
      <section className="ltc-page-intro">
        <div className="ltc-page-intro__copy">
          <div className="ltc-page-intro__eyebrow">Trust Workspace</div>
          <h1>Trust Folders</h1>
          <p>
            Vehicle: <code>{context.vehicleId}</code> · Add-on: <code>{context.addonKey}</code>
          </p>
        </div>
      </section>

      <section className="ltc-card ltc-card--compact ltc-section">
        <span className="ltc-card__eyebrow">Create</span>
        <form onSubmit={(e) => void onCreate(e)}>
          <div className="ltc-form-grid ltc-form-grid--single">
            <div className="ltc-form-group">
              <label className="ltc-form-group__label" htmlFor="trust-folder-title">
                Neuer Folder Name
                <input
                  ref={nameInputRef}
                  id="trust-folder-title"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={MAX_NAME_LENGTH}
                  className="ltc-form-group__input"
                  aria-required="true"
                  aria-invalid={errorField === "name"}
                  aria-describedby={errorField === "name" ? "trust-folder-title-error trust-folder-title-hint" : "trust-folder-title-hint"}
                />
              </label>
              <p id="trust-folder-title-hint" className="ltc-helper-text">
                Maximal {MAX_NAME_LENGTH} Zeichen.
              </p>
              {errorField === "name" && error ? (
                <p id="trust-folder-title-error" className="ltc-helper-text ltc-helper-text--error">
                  {error}
                </p>
              ) : null}
            </div>
          </div>
          <button type="submit" disabled={creating} className="ltc-button ltc-button--primary">
            {creating ? "Erstelle…" : "Folder erstellen"}
          </button>
        </form>
      </section>

      {error && errorField === null && <InlineErrorBanner message={error} />}
      {viewState === "loading" && <div className="ltc-card ltc-section">Lädt…</div>}
      {viewState === "forbidden" && <ForbiddenPanel />}
      {viewState === "addon" && <AddonRequiredPanel />}
      {viewState === "error" && !error && <InlineErrorBanner message="Unerwarteter Fehler." />}

      {viewState === "ready" && (
        <section className="ltc-card ltc-card--compact ltc-section">
          <span className="ltc-card__eyebrow">List</span>
          <h2>Liste</h2>
          {items.length === 0 ? (
            <p className="ltc-muted">Noch keine Trust-Folders vorhanden.</p>
          ) : (
            <ul className="ltc-list">
              {items.map((folder) => (
                <li key={folder.id} className="ltc-list__item">
                  <a
                    className="ltc-list__link"
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
