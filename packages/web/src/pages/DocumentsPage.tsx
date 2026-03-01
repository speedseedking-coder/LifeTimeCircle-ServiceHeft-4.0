import { FormEvent, useEffect, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";
import {
  approveDocument,
  documentDownloadHref,
  getDocument,
  listQuarantine,
  rejectDocument,
  setDocumentScanStatus,
  uploadDocument,
  type DocumentRecord,
} from "../documentsApi";

function extractCode(body: unknown): string {
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
  const code = extractCode(result.body);
  if (result.status === 413 && code === "too_large") return "Datei zu groß. Uploads sind serverseitig auf 10 MB begrenzt.";
  if (result.status === 415 && code === "ext_not_allowed") return "Dateiendung nicht erlaubt. Zulässig sind PDF, PNG, JPG und JPEG.";
  if (result.status === 415 && code === "mime_not_allowed") return "MIME-Type nicht erlaubt.";
  if (result.status === 404 && code === "not_found") return "Dokument nicht gefunden.";
  if (result.status === 409 && code === "not_scanned_clean") return "Freigabe erst nach Scan-Status CLEAN möglich.";
  if (result.status === 403 && code === "forbidden") return "Kein Zugriff auf dieses Dokument.";
  if (result.status === 403 && code === "consent_required") {
    window.location.hash = "#/consent";
    return "Consent erforderlich.";
  }
  return "Documents konnten nicht verarbeitet werden.";
}

function DocumentMetaCard(props: { title: string; doc: DocumentRecord; admin?: boolean; onRefresh?: (next: DocumentRecord) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function runAdminAction(fn: () => Promise<{ ok: true; body: DocumentRecord } | { ok: false; status: number; body?: unknown; error: string }>) {
    setBusy(true);
    setError("");
    const result = await fn();
    setBusy(false);
    if (!result.ok) {
      if (result.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(result));
      return;
    }
    props.onRefresh?.(result.body);
  }

  return (
    <section className="ltc-card ltc-section ltc-section--card">
      <h2>{props.title}</h2>
      <p>
        <strong>Datei:</strong> {props.doc.filename}
      </p>
      <p>
        <strong>ID:</strong> <code>{props.doc.id}</code>
      </p>
      <p>
        <strong>Status:</strong> {props.doc.status} · <strong>Scan:</strong> {props.doc.scan_status} · <strong>PII:</strong>{" "}
        {props.doc.pii_status}
      </p>
      <p>
        <strong>Größe:</strong> {props.doc.size_bytes} Bytes · <strong>Typ:</strong> {props.doc.content_type}
      </p>
      <p>
        <strong>Erstellt:</strong> {new Date(props.doc.created_at).toLocaleString("de-DE")}
      </p>
      <p>
        <a href={documentDownloadHref(props.doc.id)}>Download</a>
      </p>

      {props.admin ? (
        <div className="ltc-button-group">
          <button type="button" disabled={busy} onClick={() => void runAdminAction(() => setDocumentScanStatus(props.doc.id, "CLEAN"))} className="ltc-button ltc-button--secondary">
            Scan CLEAN
          </button>
          <button type="button" disabled={busy} onClick={() => void runAdminAction(() => setDocumentScanStatus(props.doc.id, "INFECTED"))} className="ltc-button ltc-button--secondary">
            Scan INFECTED
          </button>
          <button type="button" disabled={busy} onClick={() => void runAdminAction(() => approveDocument(props.doc.id))} className="ltc-button ltc-button--secondary">
            Approve
          </button>
          <button type="button" disabled={busy} onClick={() => void runAdminAction(() => rejectDocument(props.doc.id))} className="ltc-button ltc-button--secondary">
            Reject
          </button>
        </div>
      ) : null}

      {error ? <InlineErrorBanner message={error} /> : null}
    </section>
  );
}

export default function DocumentsPage(): JSX.Element {
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [recentDocs, setRecentDocs] = useState<DocumentRecord[]>([]);
  const [lookupId, setLookupId] = useState("");
  const [lookupDoc, setLookupDoc] = useState<DocumentRecord | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [adminDocs, setAdminDocs] = useState<DocumentRecord[]>([]);
  const [adminVisible, setAdminVisible] = useState(false);
  const [adminForbidden, setAdminForbidden] = useState(false);

  useEffect(() => {
    let alive = true;

    const run = async () => {
      const token = getAuthToken();
      const headers = authHeaders(token);
      const res = await listQuarantine({ headers });
      if (!alive) return;

      if (!res.ok) {
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        if (res.status === 403) {
          setAdminForbidden(true);
          setAdminVisible(false);
          return;
        }
        setError(toErrorMessage(res));
        return;
      }

      setAdminVisible(true);
      setAdminForbidden(false);
      setAdminDocs(res.body);
    };

    void run();
    return () => {
      alive = false;
    };
  }, []);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!selectedFile) {
      setError("Bitte zuerst eine Datei wählen.");
      return;
    }

    setUploading(true);
    setError("");
    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await uploadDocument(selectedFile, { headers });
    setUploading(false);

    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(res));
      return;
    }

    setRecentDocs((prev) => [res.body, ...prev.filter((doc) => doc.id !== res.body.id)].slice(0, 5));
    setLookupDoc(res.body);
    setLookupId(res.body.id);
    setSelectedFile(null);
    const input = document.getElementById("documents-upload-input") as HTMLInputElement | null;
    if (input) input.value = "";

    if (adminVisible) {
      setAdminDocs((prev) => [res.body, ...prev.filter((doc) => doc.id !== res.body.id)]);
    }
  }

  async function onLookup(e: FormEvent) {
    e.preventDefault();
    const id = lookupId.trim();
    if (!id) {
      setError("Bitte eine Dokument-ID eingeben.");
      return;
    }

    setLookupBusy(true);
    setError("");
    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await getDocument(id, { headers });
    setLookupBusy(false);

    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      if (res.status === 403) {
        setLookupDoc(null);
      }
      setError(toErrorMessage(res));
      return;
    }

    setLookupDoc(res.body);
  }

  function replaceAdminDoc(next: DocumentRecord) {
    setAdminDocs((prev) => prev.map((doc) => (doc.id === next.id ? next : doc)));
    if (lookupDoc?.id === next.id) setLookupDoc(next);
    setRecentDocs((prev) => prev.map((doc) => (doc.id === next.id ? next : doc)));
  }

  return (
    <main className="ltc-main">
      <h1>Documents</h1>
      <p>Live-Anbindung für Upload, Dokument-Abruf, Download und Admin-Quarantäne gemäß Backend-Vertrag.</p>

      <section className="ltc-card ltc-section ltc-section--card">
        <h2>Upload</h2>
        <p className="ltc-muted">Erlaubt: PDF, PNG, JPG, JPEG. Uploads starten immer als QUARANTINED + PENDING.</p>
        <form onSubmit={(e) => void onUpload(e)}>
          <input
            id="documents-upload-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            onChange={(e) => setSelectedFile(e.currentTarget.files?.[0] ?? null)}
          />
          <div className="ltc-button-group">
            <button type="submit" disabled={uploading || !selectedFile} className="ltc-button ltc-button--primary">
              {uploading ? "Lädt hoch..." : "Dokument hochladen"}
            </button>
          </div>
        </form>
      </section>

      <section className="ltc-card ltc-section ltc-section--card">
        <h2>Dokument-ID prüfen</h2>
        <form onSubmit={(e) => void onLookup(e)}>
          <input
            className="ltc-form-group__input"
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            placeholder="Dokument-ID eingeben"
            autoComplete="off"
          />
          <div className="ltc-button-group">
            <button type="submit" disabled={lookupBusy} className="ltc-button ltc-button--primary">
              {lookupBusy ? "Prüft..." : "Dokument laden"}
            </button>
          </div>
        </form>
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}

      {lookupDoc ? <DocumentMetaCard title="Geladenes Dokument" doc={lookupDoc} admin={adminVisible} onRefresh={replaceAdminDoc} /> : null}

      {recentDocs.length > 0 ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <h2>Kürzlich hochgeladen</h2>
          <ul className="ltc-list">
            {recentDocs.map((doc) => (
              <li key={doc.id} className="ltc-list__item">
                <a href={`#/documents`} className="ltc-list__link" onClick={() => setLookupDoc(doc)}>
                  {doc.filename}
                </a>{" "}
                <span className="ltc-muted">({doc.status} / {doc.scan_status})</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {adminVisible ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <h2>Admin-Quarantäne</h2>
          {adminDocs.length === 0 ? (
            <p className="ltc-muted">Keine Dokumente in Quarantäne.</p>
          ) : (
            adminDocs.map((doc) => (
              <DocumentMetaCard key={doc.id} title={`Quarantäne: ${doc.filename}`} doc={doc} admin onRefresh={replaceAdminDoc} />
            ))
          )}
        </section>
      ) : null}

      {adminForbidden ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <h2>Admin-Quarantäne</h2>
          <p className="ltc-muted">Admin-Review ist für die aktuelle Rolle nicht sichtbar.</p>
        </section>
      ) : null}

      <section className="ltc-section">
        <h2>Navigation (Hash)</h2>
        <ul className="ltc-list">
          <li className="ltc-list__item">
            <a href="#/vehicles" className="ltc-list__link">Zu Vehicles</a>
          </li>
          <li className="ltc-list__item">
            <a href="#/onboarding" className="ltc-list__link">Zu Onboarding</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
