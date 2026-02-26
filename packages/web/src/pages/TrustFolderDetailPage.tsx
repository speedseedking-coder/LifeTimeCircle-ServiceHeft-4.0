import { FormEvent, useEffect, useMemo, useState } from "react";
import { authHeaders, getAuthToken } from "../lib.auth";
import { deleteTrustFolder, listTrustFolders, renameTrustFolder, TrustFolder } from "../api";
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

  const hash = useHash();
  const context = useMemo(() => readTrustFolderContextFromHash(hash), [hash]);

  const folderIdNum = useMemo(() => {
    const n = Number(props.folderId);
    return Number.isFinite(n) ? n : NaN;
  }, [props.folderId]);

  useEffect(() => {
    let alive = true;

    if (!context.vehicleId) {
      setViewState("error");
      setError("Vehicle-Kontext fehlt.");
      return () => {
        alive = false;
      };
    }
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

      const res = await listTrustFolders(context.vehicleId, context.addonKey, { headers });
      if (!alive) return;

      if (!res.ok) {
        handleApiNotOk(res, { setViewState, setError, fallbackError: "Trust-Folder konnte nicht geladen werden." });
        return;
      }

      const target = res.body.find((x) => x.id === folderIdNum) ?? null;
      if (!target) {
        setViewState("error");
        setError("Trust-Folder wurde nicht gefunden.");
        return;
      }

      setFolder(target);
      setTitle(target.title);
      setViewState("ready");
    };

    void run();
    return () => {
      alive = false;
    };
  }, [context.vehicleId, context.addonKey, folderIdNum]);

  async function onRename(e: FormEvent) {
    e.preventDefault();
    if (!folder) return;

    const nextTitle = title.trim();
    if (nextTitle.length < 1 || nextTitle.length > MAX_NAME_LENGTH) {
      setError(`Name muss zwischen 1 und ${MAX_NAME_LENGTH} Zeichen liegen.`);
      return;
    }

    setError("");
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

    window.location.hash = `#/trust-folders?vehicle_id=${encodeURIComponent(context.vehicleId)}&addon_key=${encodeURIComponent(
      context.addonKey,
    )}`;
  }

  if (!context.vehicleId) {
    return (
      <main style={{ padding: 12 }}>
        <div className="ltc-card" role="status">
          <div className="ltc-card__title">Bitte Vehicle wählen</div>
          <div className="ltc-muted">Für Trust-Folder-Details wird ein Vehicle-Kontext benötigt.</div>
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
      <a
        className="ltc-link"
        href={`#/trust-folders?vehicle_id=${encodeURIComponent(context.vehicleId)}&addon_key=${encodeURIComponent(
          context.addonKey,
        )}`}
      >
        ← Zurück zur Liste
      </a>

      {error && <InlineErrorBanner message={error} />}
      {viewState === "loading" && <div className="ltc-card">Lädt…</div>}
      {viewState === "forbidden" && <ForbiddenPanel />}
      {viewState === "addon" && <AddonRequiredPanel />}

      {viewState === "ready" && folder && (
        <section className="ltc-card" style={{ marginTop: 12 }}>
          <h1>{folder.title}</h1>

          <form onSubmit={(e) => void onRename(e)}>
            <label htmlFor="trust-folder-title">Name</label>
            <input
              id="trust-folder-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={MAX_NAME_LENGTH}
              style={{ width: "100%", marginTop: 8, padding: 10 }}
            />
            <button type="submit" style={{ marginTop: 10, padding: "8px 12px" }}>
              Speichern
            </button>
          </form>

          <button
            type="button"
            onClick={() => void onDelete()}
            style={{ marginTop: 10, padding: "8px 12px", borderColor: "rgba(255,120,120,0.6)" }}
          >
            Löschen
          </button>
        </section>
      )}
    </main>
  );
}