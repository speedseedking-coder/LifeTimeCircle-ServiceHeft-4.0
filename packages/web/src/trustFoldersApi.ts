import { httpFetch } from "./lib/httpFetch";

export type TrustFolder = {
  id: number;
  vehicle_id: string;
  owner_user_id: string;
  addon_key: string;
  title: string;
};

export type TrustApiResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; body?: unknown; error: string };

function normalizePath(path: string): string {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

async function readBody(res: Response): Promise<unknown> {
  const ct = (res.headers.get("content-type") ?? "").toLowerCase();
  if (ct.includes("application/json")) {
    try { return await res.json(); } catch { /* fallthrough */ }
  }
  try { return await res.text(); } catch { return undefined; }
}

async function request<T>(method: "GET" | "POST" | "PATCH" | "DELETE", path: string, init?: RequestInit, body?: unknown): Promise<TrustApiResult<T>> {
  const url = `/api${normalizePath(path)}`;

  const headers: Record<string, string> = {
    Accept: "application/json, text/plain, */*",
    ...(init?.headers as any),
  };

  const hasBody = typeof body !== "undefined";
  const finalInit: RequestInit = {
    ...init,
    method,
    headers: {
      ...headers,
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
    },
    body: hasBody ? JSON.stringify(body) : init?.body,
  };

  let res: Response;
  try {
    res = await httpFetch(url, finalInit);
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

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function mapTrustFolderBody(body: unknown): TrustFolder | null {
  if (!isRecord(body)) return null;
  if (typeof body.id !== "number") return null;
  if (typeof body.vehicle_id !== "string") return null;
  if (typeof body.owner_user_id !== "string") return null;
  if (typeof body.addon_key !== "string") return null;
  if (typeof body.title !== "string") return null;
  return body as TrustFolder;
}

function encodeQuery(params: Record<string, string>): string {
  return Object.entries(params).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
}

export async function listTrustFolders(vehicleId: string, addonKey = "restauration", init?: RequestInit): Promise<TrustApiResult<TrustFolder[]>> {
  const q = encodeQuery({ vehicle_id: vehicleId, addon_key: addonKey });
  const res = await request<unknown>("GET", `/trust/folders?${q}`, init);
  if (!res.ok) return res;

  if (!Array.isArray(res.body)) return { ok: false, status: 500, error: "invalid_body", body: res.body };

  const mapped: TrustFolder[] = [];
  for (const item of res.body) {
    const f = mapTrustFolderBody(item);
    if (f) mapped.push(f);
  }
  return { ok: true, status: res.status, body: mapped };
}

export async function createTrustFolder(vehicleId: string, title: string, addonKey = "restauration", init?: RequestInit): Promise<TrustApiResult<TrustFolder>> {
  const res = await request<unknown>("POST", "/trust/folders", init, { vehicle_id: vehicleId, title, addon_key: addonKey });
  if (!res.ok) return res;
  const mapped = mapTrustFolderBody(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function getTrustFolder(id: number, init?: RequestInit): Promise<TrustApiResult<TrustFolder>> {
  const res = await request<unknown>("GET", `/trust/folders/${id}`, init);
  if (!res.ok) return res;
  const mapped = mapTrustFolderBody(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function renameTrustFolder(id: number, title: string, init?: RequestInit): Promise<TrustApiResult<TrustFolder>> {
  const res = await request<unknown>("PATCH", `/trust/folders/${id}`, init, { title });
  if (!res.ok) return res;
  const mapped = mapTrustFolderBody(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function deleteTrustFolder(id: number, init?: RequestInit): Promise<TrustApiResult<{ ok: true }>> {
  const res = await request<unknown>("DELETE", `/trust/folders/${id}`, init);
  if (!res.ok) return res;
  return { ok: true, status: res.status, body: { ok: true } };
}
