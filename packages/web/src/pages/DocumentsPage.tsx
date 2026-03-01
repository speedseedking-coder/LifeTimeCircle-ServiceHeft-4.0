import { FormEvent, useEffect, useMemo, useState } from "react";
import { Badge, type BadgeVariant } from "../components/ui/Badge";
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

type DocumentStats = {
  total: number;
  totalSize: number;
  byStatus: Record<string, number>;
  byScanStatus: Record<string, number>;
  byPiiStatus: Record<string, number>;
  byContentType: Record<string, number>;
};

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

/* ========== DOCUMENT STATS & ANALYTICS ========== */

function calculateDocumentStats(docs: DocumentRecord[]): DocumentStats {
  const stats: DocumentStats = {
    total: docs.length,
    totalSize: 0,
    byStatus: {},
    byScanStatus: {},
    byPiiStatus: {},
    byContentType: {},
  };

  for (const doc of docs) {
    stats.totalSize += doc.size_bytes;
    stats.byStatus[doc.status] = (stats.byStatus[doc.status] ?? 0) + 1;
    stats.byScanStatus[doc.scan_status] = (stats.byScanStatus[doc.scan_status] ?? 0) + 1;
    stats.byPiiStatus[doc.pii_status] = (stats.byPiiStatus[doc.pii_status] ?? 0) + 1;

    const mimeType = doc.content_type?.split("/")?.[1] || "unknown";
    stats.byContentType[mimeType] = (stats.byContentType[mimeType] ?? 0) + 1;
  }

  return stats;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 10) / 10 + " " + sizes[i];
}

function getStatusVariant(status: string): BadgeVariant {
  if (status === "APPROVED" || status === "CLEAN" || status === "OK") return "success";
  if (status === "REJECTED" || status === "INFECTED" || status === "CONFIRMED") return "error";
  if (status === "QUARANTINED" || status === "PENDING" || status === "SUSPECTED") return "warning";
  return "neutral";
}

function renderStatBadges(values: Record<string, number>): JSX.Element[] {
  return Object.entries(values)
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([label, count]) => (
      <Badge key={label} variant={getStatusVariant(label)} size="sm">
        {label}: {count}
      </Badge>
    ));
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
  const [errorField, setErrorField] = useState<"upload" | "lookup" | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [recentDocs, setRecentDocs] = useState<DocumentRecord[]>([]);
  const [lookupId, setLookupId] = useState("");
  const [lookupDoc, setLookupDoc] = useState<DocumentRecord | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [adminDocs, setAdminDocs] = useState<DocumentRecord[]>([]);
  const [adminVisible, setAdminVisible] = useState(false);
  const [adminForbidden, setAdminForbidden] = useState(false);
  const docStats = useMemo(
    () =>
      calculateDocumentStats([
        ...recentDocs,
        ...adminDocs,
        ...(lookupDoc && !recentDocs.includes(lookupDoc) && !adminDocs.includes(lookupDoc) ? [lookupDoc] : []),
      ]),
    [recentDocs, adminDocs, lookupDoc],
  );

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
      setErrorField("upload");
      return;
    }

    setUploading(true);
    setError("");
    setErrorField(null);
    const token = getAuthToken();
    const headers = authHeaders(token);
    const res = await uploadDocument(selectedFile, { headers });
    setUploading(false);

    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      setErrorField("upload");
      setError(toErrorMessage(res));
      return;
    }

    setRecentDocs((prev) => [res.body, ...prev.filter((doc) => doc.id !== res.body.id)].slice(0, 5));
    setLookupDoc(res.body);
    setLookupId(res.body.id);
    setSelectedFile(null);
    setErrorField(null);
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
      setErrorField("lookup");
      return;
    }

    setLookupBusy(true);
    setError("");
    setErrorField(null);
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
      setErrorField("lookup");
      setError(toErrorMessage(res));
      return;
    }

    setLookupDoc(res.body);
    setErrorField(null);
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
          <label className="ltc-form-group__label" htmlFor="documents-upload-input">
            Dokument auswählen
          </label>
          <input
            id="documents-upload-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            aria-label="Dokument für Upload auswählen"
            aria-required="true"
            aria-invalid={errorField === "upload"}
            aria-describedby={errorField === "upload" ? "documents-upload-error" : undefined}
            onChange={(e) => setSelectedFile(e.currentTarget.files?.[0] ?? null)}
          />
          <div className="ltc-button-group">
            <button type="submit" disabled={uploading || !selectedFile} className="ltc-button ltc-button--primary">
              {uploading ? "Lädt hoch..." : "Dokument hochladen"}
            </button>
          </div>
          {errorField === "upload" && error ? (
            <p id="documents-upload-error" className="ltc-helper-text ltc-helper-text--error">
              {error}
            </p>
          ) : null}
        </form>
      </section>

      <section className="ltc-card ltc-section ltc-section--card">
        <h2>Dokument-ID prüfen</h2>
        <form onSubmit={(e) => void onLookup(e)}>
          <label className="ltc-form-group__label" htmlFor="documents-lookup-input">
            Dokument-ID
          </label>
          <input
            id="documents-lookup-input"
            className="ltc-form-group__input"
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            placeholder="Dokument-ID eingeben"
            autoComplete="off"
            aria-required="true"
            aria-invalid={errorField === "lookup"}
            aria-describedby={errorField === "lookup" ? "documents-lookup-error" : undefined}
          />
          <div className="ltc-button-group">
            <button type="submit" disabled={lookupBusy} className="ltc-button ltc-button--primary">
              {lookupBusy ? "Prüft..." : "Dokument laden"}
            </button>
          </div>
          {errorField === "lookup" && error ? (
            <p id="documents-lookup-error" className="ltc-helper-text ltc-helper-text--error">
              {error}
            </p>
          ) : null}
        </form>
      </section>

      {docStats.total > 0 ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <h2>Dokumentenstatus</h2>
          <div className="ltc-grid ltc-grid--3">
            <div>
              <strong>Gesamt</strong>
              <p className="ltc-muted">{docStats.total} Dokumente im aktuellen Arbeitskontext</p>
            </div>
            <div>
              <strong>Volumen</strong>
              <p className="ltc-muted">{formatBytes(docStats.totalSize)} Gesamtdatenmenge</p>
            </div>
            <div>
              <strong>Formate</strong>
              <div className="ltc-flex ltc-flex--wrap ltc-mt-2">{renderStatBadges(docStats.byContentType)}</div>
            </div>
          </div>
          <div className="ltc-grid ltc-grid--3 ltc-mt-4">
            <div>
              <strong>Freigabe</strong>
              <div className="ltc-flex ltc-flex--wrap ltc-mt-2">{renderStatBadges(docStats.byStatus)}</div>
            </div>
            <div>
              <strong>Scan</strong>
              <div className="ltc-flex ltc-flex--wrap ltc-mt-2">{renderStatBadges(docStats.byScanStatus)}</div>
            </div>
            <div>
              <strong>PII</strong>
              <div className="ltc-flex ltc-flex--wrap ltc-mt-2">{renderStatBadges(docStats.byPiiStatus)}</div>
            </div>
          </div>
        </section>
      ) : null}

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
