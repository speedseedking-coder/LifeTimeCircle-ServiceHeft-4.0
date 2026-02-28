import { httpFetch } from "./lib/httpFetch";

export type DocumentRecord = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: string;
  scan_status: string;
  pii_status: string;
  created_at: string;
  created_by_user_id: string | null;
};

export type DocumentsApiResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; body?: unknown; error: string };

function normalizePath(path: string): string {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

async function readBody(res: Response): Promise<unknown> {
  const ct = (res.headers.get("content-type") ?? "").toLowerCase();
  if (ct.includes("application/json")) {
    try {
      return await res.json();
    } catch {
      // fall through
    }
  }
  try {
    return await res.text();
  } catch {
    return undefined;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function mapDocument(body: unknown): DocumentRecord | null {
  if (!isRecord(body)) return null;
  if (typeof body.id !== "string") return null;
  if (typeof body.filename !== "string") return null;
  if (typeof body.content_type !== "string") return null;
  if (typeof body.size_bytes !== "number") return null;
  const status = typeof body.status === "string" ? body.status : typeof body.approval_status === "string" ? body.approval_status : null;
  if (!status) return null;
  if (typeof body.scan_status !== "string") return null;
  if (typeof body.pii_status !== "string") return null;
  if (typeof body.created_at !== "string") return null;

  return {
    id: body.id,
    filename: body.filename,
    content_type: body.content_type,
    size_bytes: body.size_bytes,
    status,
    scan_status: body.scan_status,
    pii_status: body.pii_status,
    created_at: body.created_at,
    created_by_user_id: typeof body.created_by_user_id === "string" ? body.created_by_user_id : null,
  };
}

async function request<T>(method: string, path: string, init?: RequestInit): Promise<DocumentsApiResult<T>> {
  const url = `/api${normalizePath(path)}`;

  let res: Response;
  try {
    res = await httpFetch(url, init ? { ...init, method } : { method });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, status: 0, error: `network_error: ${msg}` };
  }

  const parsed = await readBody(res);
  if (!res.ok) {
    return { ok: false, status: res.status, error: `http_${res.status}`, body: parsed };
  }

  return { ok: true, status: res.status, body: parsed as T };
}

export async function uploadDocument(file: File, init?: RequestInit): Promise<DocumentsApiResult<DocumentRecord>> {
  const formData = new FormData();
  formData.set("file", file);

  const res = await request<unknown>("POST", "/documents/upload", {
    ...init,
    body: formData,
  });
  if (!res.ok) return res;

  const mapped = mapDocument(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function getDocument(id: string, init?: RequestInit): Promise<DocumentsApiResult<DocumentRecord>> {
  const res = await request<unknown>("GET", `/documents/${encodeURIComponent(id)}`, init);
  if (!res.ok) return res;
  const mapped = mapDocument(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function listQuarantine(init?: RequestInit): Promise<DocumentsApiResult<DocumentRecord[]>> {
  const res = await request<unknown>("GET", "/documents/admin/quarantine", init);
  if (!res.ok) return res;
  if (!Array.isArray(res.body)) return { ok: false, status: 500, error: "invalid_body", body: res.body };

  const mapped: DocumentRecord[] = [];
  for (const item of res.body) {
    const doc = mapDocument(item);
    if (doc) mapped.push(doc);
  }
  return { ok: true, status: res.status, body: mapped };
}

export async function setDocumentScanStatus(
  id: string,
  scanStatus: "PENDING" | "CLEAN" | "INFECTED" | "ERROR",
  init?: RequestInit,
): Promise<DocumentsApiResult<DocumentRecord>> {
  const res = await request<unknown>("POST", `/documents/${encodeURIComponent(id)}/scan`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    },
    body: JSON.stringify({ scan_status: scanStatus }),
  });
  if (!res.ok) return res;
  const mapped = mapDocument(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function approveDocument(id: string, init?: RequestInit): Promise<DocumentsApiResult<DocumentRecord>> {
  const res = await request<unknown>("POST", `/documents/${encodeURIComponent(id)}/approve`, init);
  if (!res.ok) return res;
  const mapped = mapDocument(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function rejectDocument(id: string, init?: RequestInit): Promise<DocumentsApiResult<DocumentRecord>> {
  const res = await request<unknown>("POST", `/documents/${encodeURIComponent(id)}/reject`, init);
  if (!res.ok) return res;
  const mapped = mapDocument(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export function documentDownloadHref(id: string): string {
  return `/api/documents/${encodeURIComponent(id)}/download`;
}
