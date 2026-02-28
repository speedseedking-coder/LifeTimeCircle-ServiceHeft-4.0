import { httpFetch } from "./lib/httpFetch";

export type Vehicle = {
  id: string;
  vin_masked: string;
  nickname: string | null;
  meta: Record<string, unknown> | null;
};

export type VehicleTrustSummary = {
  trust_light: "rot" | "orange" | "gelb" | "gruen";
  hint: string;
  reason_codes: string[];
  todo_codes: string[];
  verification_level: "niedrig" | "mittel" | "hoch";
  accident_status: "unfallfrei" | "nicht_unfallfrei" | "unbekannt";
  accident_status_label: string;
  history_status: "vorhanden" | "nicht_vorhanden";
  evidence_status: "vorhanden" | "nicht_vorhanden";
  top_trust_level: "T1" | "T2" | "T3" | null;
};

export type VehicleEntry = {
  id: string;
  vehicle_id: string;
  entry_group_id: string;
  supersedes_entry_id: string | null;
  version: number;
  revision_count: number;
  is_latest: boolean;
  date: string;
  type: string;
  performed_by: string;
  km: number;
  note: string | null;
  cost_amount: number | null;
  trust_level: "T1" | "T2" | "T3" | null;
  created_at: string;
  updated_at: string;
};

export type VehicleEntryInput = {
  date: string;
  type: string;
  performed_by: string;
  km: number;
  note?: string | null;
  cost_amount?: number | null;
  trust_level?: "T1" | "T2" | "T3" | null;
};

export type VehicleApiResult<T> =
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

function mapVehicle(body: unknown): Vehicle | null {
  if (!isRecord(body)) return null;
  if (typeof body.id !== "string") return null;
  if (typeof body.vin_masked !== "string") return null;
  const nickname = typeof body.nickname === "string" ? body.nickname : null;
  const meta = isRecord(body.meta) ? body.meta : null;
  return {
    id: body.id,
    vin_masked: body.vin_masked,
    nickname,
    meta,
  };
}

function mapVehicleEntry(body: unknown): VehicleEntry | null {
  if (!isRecord(body)) return null;
  if (
    typeof body.id !== "string" ||
    typeof body.vehicle_id !== "string" ||
    typeof body.entry_group_id !== "string" ||
    typeof body.version !== "number" ||
    typeof body.revision_count !== "number" ||
    typeof body.is_latest !== "boolean" ||
    typeof body.date !== "string" ||
    typeof body.type !== "string" ||
    typeof body.performed_by !== "string" ||
    typeof body.km !== "number" ||
    typeof body.created_at !== "string" ||
    typeof body.updated_at !== "string"
  ) {
    return null;
  }

  const supersedes_entry_id = typeof body.supersedes_entry_id === "string" ? body.supersedes_entry_id : null;
  const note = typeof body.note === "string" ? body.note : null;
  const cost_amount = typeof body.cost_amount === "number" ? body.cost_amount : null;
  const trust_level = body.trust_level === "T1" || body.trust_level === "T2" || body.trust_level === "T3" ? body.trust_level : null;

  return {
    id: body.id,
    vehicle_id: body.vehicle_id,
    entry_group_id: body.entry_group_id,
    supersedes_entry_id,
    version: body.version,
    revision_count: body.revision_count,
    is_latest: body.is_latest,
    date: body.date,
    type: body.type,
    performed_by: body.performed_by,
    km: body.km,
    note,
    cost_amount,
    trust_level,
    created_at: body.created_at,
    updated_at: body.updated_at,
  };
}

function mapVehicleTrustSummary(body: unknown): VehicleTrustSummary | null {
  if (!isRecord(body)) return null;
  if (
    (body.trust_light !== "rot" && body.trust_light !== "orange" && body.trust_light !== "gelb" && body.trust_light !== "gruen") ||
    typeof body.hint !== "string" ||
    !Array.isArray(body.reason_codes) ||
    !Array.isArray(body.todo_codes) ||
    (body.verification_level !== "niedrig" && body.verification_level !== "mittel" && body.verification_level !== "hoch") ||
    (body.accident_status !== "unfallfrei" && body.accident_status !== "nicht_unfallfrei" && body.accident_status !== "unbekannt") ||
    typeof body.accident_status_label !== "string" ||
    (body.history_status !== "vorhanden" && body.history_status !== "nicht_vorhanden") ||
    (body.evidence_status !== "vorhanden" && body.evidence_status !== "nicht_vorhanden")
  ) {
    return null;
  }

  const top_trust_level = body.top_trust_level === "T1" || body.top_trust_level === "T2" || body.top_trust_level === "T3" ? body.top_trust_level : null;

  return {
    trust_light: body.trust_light,
    hint: body.hint,
    reason_codes: body.reason_codes.filter((item): item is string => typeof item === "string"),
    todo_codes: body.todo_codes.filter((item): item is string => typeof item === "string"),
    verification_level: body.verification_level,
    accident_status: body.accident_status,
    accident_status_label: body.accident_status_label,
    history_status: body.history_status,
    evidence_status: body.evidence_status,
    top_trust_level,
  };
}

async function request<T>(method: "GET" | "POST", path: string, init?: RequestInit, body?: unknown): Promise<VehicleApiResult<T>> {
  const url = `/api${normalizePath(path)}`;
  const hasBody = typeof body !== "undefined";

  let res: Response;
  try {
    res = await httpFetch(url, {
      ...init,
      method,
      headers: {
        Accept: "application/json, text/plain, */*",
        ...(init?.headers as Record<string, string> | undefined),
        ...(hasBody ? { "Content-Type": "application/json" } : {}),
      },
      body: hasBody ? JSON.stringify(body) : init?.body,
    });
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

async function mapVehicleEntryListResult(res: VehicleApiResult<unknown>): Promise<VehicleApiResult<VehicleEntry[]>> {
  if (!res.ok) return res;
  if (!Array.isArray(res.body)) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  const mapped: VehicleEntry[] = [];
  for (const item of res.body) {
    const entry = mapVehicleEntry(item);
    if (entry) mapped.push(entry);
  }
  return { ok: true, status: res.status, body: mapped };
}

export async function listVehicles(init?: RequestInit): Promise<VehicleApiResult<Vehicle[]>> {
  const res = await request<unknown>("GET", "/vehicles", init);
  if (!res.ok) return res;
  if (!Array.isArray(res.body)) return { ok: false, status: 500, error: "invalid_body", body: res.body };

  const mapped: Vehicle[] = [];
  for (const item of res.body) {
    const vehicle = mapVehicle(item);
    if (vehicle) mapped.push(vehicle);
  }
  return { ok: true, status: res.status, body: mapped };
}

export async function getVehicle(id: string, init?: RequestInit): Promise<VehicleApiResult<Vehicle>> {
  const res = await request<unknown>("GET", `/vehicles/${encodeURIComponent(id)}`, init);
  if (!res.ok) return res;
  const mapped = mapVehicle(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function createVehicle(
  payload: { vin: string; nickname?: string | null; meta?: Record<string, unknown> | null },
  init?: RequestInit,
): Promise<VehicleApiResult<Vehicle>> {
  const body: Record<string, unknown> = {
    vin: payload.vin,
  };
  if (payload.nickname && payload.nickname.trim().length > 0) {
    body.nickname = payload.nickname.trim();
  }
  if (payload.meta && isRecord(payload.meta)) {
    body.meta = payload.meta;
  }

  const res = await request<unknown>("POST", "/vehicles", init, body);
  if (!res.ok) return res;
  const mapped = mapVehicle(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function getVehicleTrustSummary(id: string, init?: RequestInit): Promise<VehicleApiResult<VehicleTrustSummary>> {
  const res = await request<unknown>("GET", `/vehicles/${encodeURIComponent(id)}/trust-summary`, init);
  if (!res.ok) return res;
  const mapped = mapVehicleTrustSummary(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function listVehicleEntries(vehicleId: string, init?: RequestInit): Promise<VehicleApiResult<VehicleEntry[]>> {
  const res = await request<unknown>("GET", `/vehicles/${encodeURIComponent(vehicleId)}/entries`, init);
  return mapVehicleEntryListResult(res);
}

export async function getVehicleEntryHistory(vehicleId: string, entryId: string, init?: RequestInit): Promise<VehicleApiResult<VehicleEntry[]>> {
  const res = await request<unknown>("GET", `/vehicles/${encodeURIComponent(vehicleId)}/entries/${encodeURIComponent(entryId)}/history`, init);
  return mapVehicleEntryListResult(res);
}

function normalizeEntryInput(payload: VehicleEntryInput): Record<string, unknown> {
  const body: Record<string, unknown> = {
    date: payload.date,
    type: payload.type,
    performed_by: payload.performed_by,
    km: payload.km,
  };
  if (typeof payload.note === "string" && payload.note.trim().length > 0) body.note = payload.note.trim();
  if (typeof payload.cost_amount === "number" && Number.isFinite(payload.cost_amount)) body.cost_amount = payload.cost_amount;
  if (payload.trust_level === "T1" || payload.trust_level === "T2" || payload.trust_level === "T3") body.trust_level = payload.trust_level;
  return body;
}

export async function createVehicleEntry(
  vehicleId: string,
  payload: VehicleEntryInput,
  init?: RequestInit,
): Promise<VehicleApiResult<VehicleEntry>> {
  const res = await request<unknown>("POST", `/vehicles/${encodeURIComponent(vehicleId)}/entries`, init, normalizeEntryInput(payload));
  if (!res.ok) return res;
  const mapped = mapVehicleEntry(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}

export async function createVehicleEntryRevision(
  vehicleId: string,
  entryId: string,
  payload: VehicleEntryInput,
  init?: RequestInit,
): Promise<VehicleApiResult<VehicleEntry>> {
  const res = await request<unknown>(
    "POST",
    `/vehicles/${encodeURIComponent(vehicleId)}/entries/${encodeURIComponent(entryId)}/revisions`,
    init,
    normalizeEntryInput(payload),
  );
  if (!res.ok) return res;
  const mapped = mapVehicleEntry(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}
