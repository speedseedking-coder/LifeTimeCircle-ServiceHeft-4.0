import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { authHeaders, getAuthToken } from "../lib.auth";
import { deleteTrustFolder, getTrustFolder, renameTrustFolder, TrustFolder } from "../trustFoldersApi";
import ForbiddenPanel from "../components/ForbiddenPanel";
import AddonRequiredPanel from "../components/AddonRequiredPanel";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { useHash } from "../hooks/useHash";
import { readTrustFolderContextFromHash } from "../lib/trustFolderContext";
import { handleApiNotOk } from "../lib/handleApiGates";

type ViewState = "loading" | "ready" | "forbidden" | "addon" | "error";
const MAX_NAME_LENGTH = 80;

export default function TrustFolderDetailPage(props: { folderId: string }): JSX.Element {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [folder, setFolder] = useState<TrustFolder | null>(null);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState<"title" | null>(null);
  const titleInputRef = useRef<HTMLInputElement | null>(null);

  const hash = useHash();
  const context = useMemo(() => readTrustFolderContextFromHash(hash), [hash]);

  const folderIdNum = useMemo(() => {
    const n = Number(props.folderId);
    return Number.isFinite(n) ? n : NaN;
  }, [props.folderId]);
  const resolvedVehicleId = folder?.vehicle_id ?? context.vehicleId;
  const resolvedAddonKey = folder?.addon_key ?? context.addonKey;

  useEffect(() => {
    if (viewState === "ready" && folder) {
      titleInputRef.current?.focus();
    }
  }, [viewState, folder]);

  useEffect(() => {
    let alive = true;

    if (!Number.isFinite(folderIdNum)) {
      setViewState("error");
      setError("Ungültige Trust-Folder-ID.");
      return () => {
        alive = false;
      };
    }

    const run = async () => {
      setViewState("loading");
      setError("");

      const token = getAuthToken();
      const headers = authHeaders(token);

      const res = await getTrustFolder(folderIdNum, { headers });
      if (!alive) return;

      if (!res.ok) {
        handleApiNotOk(res, { setViewState, setError, fallbackError: "Trust-Folder konnte nicht geladen werden." });
        return;
      }

      setFolder(res.body);
      setTitle(res.body.title);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, [folderIdNum]);

  async function onRename(e: FormEvent) {
    e.preventDefault();
    if (!folder) return;

    const nextTitle = title.trim();
    if (nextTitle.length < 1 || nextTitle.length > MAX_NAME_LENGTH) {
      setError(`Name muss zwischen 1 und ${MAX_NAME_LENGTH} Zeichen liegen.`);
      setErrorField("title");
      titleInputRef.current?.focus();
      return;
    }

    setError("");
    setErrorField(null);
    const token = getAuthToken();
    const headers = authHeaders(token);

    const res = await renameTrustFolder(folder.id, nextTitle, { headers });
    if (!res.ok) {
      handleApiNotOk(res, { setViewState, setError, fallbackError: "Umbenennen fehlgeschlagen." });
      return;
    }

    setFolder(res.body);
    setTitle(res.body.title);
  }

  async function onDelete() {
    if (!folder) return;
    const ok = window.confirm("Trust-Folder wirklich löschen?");
    if (!ok) return;

    setError("");
    const token = getAuthToken();
    const headers = authHeaders(token);

    const res = await deleteTrustFolder(folder.id, { headers });
    if (!res.ok) {
      handleApiNotOk(res, { setViewState, setError, fallbackError: "Löschen fehlgeschlagen." });
      return;
    }

    window.location.hash = `#/trust-folders?vehicle_id=${encodeURIComponent(resolvedVehicleId)}&addon_key=${encodeURIComponent(
      resolvedAddonKey,
    )}`;
  }

  if (!resolvedVehicleId && viewState !== "loading") {
    return (
      <main className="ltc-main ltc-main--narrow">
        <div className="ltc-card" role="status">
          <div className="ltc-card__title">Bitte Vehicle wählen</div>
          <div className="ltc-muted">Für Trust-Folder-Details wird ein Vehicle-Kontext benötigt.</div>
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
    <main className="ltc-main ltc-main--narrow" data-testid="trust-folder-detail-page">
      {resolvedVehicleId ? (
        <a
          className="ltc-link"
          href={`#/trust-folders?vehicle_id=${encodeURIComponent(resolvedVehicleId)}&addon_key=${encodeURIComponent(
            resolvedAddonKey,
          )}`}
        >
          ← Zurück zur Liste
        </a>
      ) : null}

      {error && errorField === null ? <InlineErrorBanner message={error} /> : null}
      {viewState === "loading" && <div className="ltc-card ltc-section">Lädt…</div>}
      {viewState === "forbidden" && <ForbiddenPanel />}
      {viewState === "addon" && <AddonRequiredPanel />}

      {viewState === "ready" && folder && (
        <section className="ltc-card ltc-card--compact ltc-section">
          <span className="ltc-card__eyebrow">Detail</span>
          <h1>{folder.title}</h1>

          <form onSubmit={(e) => void onRename(e)}>
            <div className="ltc-form-grid ltc-form-grid--single">
              <div className="ltc-form-group">
                <label className="ltc-form-group__label" htmlFor="trust-folder-detail-title">
                  Name
                  <input
                    ref={titleInputRef}
                    id="trust-folder-detail-title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    maxLength={MAX_NAME_LENGTH}
                    className="ltc-form-group__input"
                    aria-required="true"
                    aria-invalid={errorField === "title"}
                    aria-describedby={errorField === "title" ? "trust-folder-detail-error trust-folder-detail-hint" : "trust-folder-detail-hint"}
                  />
                </label>
                <p id="trust-folder-detail-hint" className="ltc-helper-text">
                  Name zwischen 1 und {MAX_NAME_LENGTH} Zeichen.
                </p>
                {errorField === "title" && error ? (
                  <p id="trust-folder-detail-error" className="ltc-helper-text ltc-helper-text--error">
                    {error}
                  </p>
                ) : null}
              </div>
            </div>
            <button type="submit" className="ltc-button ltc-button--primary">
              Speichern
            </button>
          </form>

          <button
            type="button"
            onClick={() => void onDelete()}
            className="ltc-button ltc-button--secondary ltc-mt-4"
            aria-label={`Trust-Folder ${folder.title} löschen`}
          >
            Löschen
          </button>
        </section>
      )}
    </main>
  );
}
