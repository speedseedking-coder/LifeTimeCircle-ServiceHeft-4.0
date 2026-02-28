import { httpFetch } from "./lib/httpFetch";

export type Vehicle = {
  id: string;
  vin_masked: string;
  nickname: string | null;
  meta: Record<string, unknown> | null;
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
  payload: { vin: string; nickname?: string | null },
  init?: RequestInit,
): Promise<VehicleApiResult<Vehicle>> {
  const body: Record<string, unknown> = {
    vin: payload.vin,
  };
  if (payload.nickname && payload.nickname.trim().length > 0) {
    body.nickname = payload.nickname.trim();
  }

  const res = await request<unknown>("POST", "/vehicles", init, body);
  if (!res.ok) return res;
  const mapped = mapVehicle(res.body);
  if (!mapped) return { ok: false, status: 500, error: "invalid_body", body: res.body };
  return { ok: true, status: res.status, body: mapped };
}
