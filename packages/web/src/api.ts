export type ApiBody = unknown | string;

export type ApiResult =
  | {
      ok: true;
      status: number;
      contentType: string | null;
      body: ApiBody;
    }
  | {
      ok: false;
      status: number;
      contentType: string | null;
      error: string;
      body?: ApiBody;
    };

function normalizePath(path: string): string {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

async function readBody(res: Response): Promise<{ contentType: string | null; body: ApiBody }> {
  const contentType = res.headers.get("content-type");
  const isJson = (contentType ?? "").toLowerCase().includes("application/json");

  if (isJson) {
    try {
      return { contentType, body: (await res.json()) as unknown };
    } catch {
      // Fallback: invalid JSON
    }
  }

  return { contentType, body: await res.text() };
}

async function apiRequest(method: "GET" | "POST", path: string, init?: RequestInit): Promise<ApiResult> {
  const url = `/api${normalizePath(path)}`;

  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers: {
        Accept: "application/json, text/plain, text/html;q=0.9, */*;q=0.8",
        // Content-Type nur setzen, wenn wir wirklich JSON-String senden (future-safe für FormData)
        ...((typeof init?.body === "string" && init.body.length > 0) ? { "Content-Type": "application/json" } : {}),
        ...(init?.headers ?? {}),
      },
      ...init,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, status: 0, contentType: null, error: `network_error: ${msg}` };
  }

  const { contentType, body } = await readBody(res);

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      contentType,
      error: `http_${res.status}`,
      body,
    };
  }

  return { ok: true, status: res.status, contentType, body };
}

export async function apiGet(path: string, init?: RequestInit): Promise<ApiResult> {
  return apiRequest("GET", path, init);
}

export async function apiPost(path: string, body?: unknown, init?: RequestInit): Promise<ApiResult> {
  return apiRequest("POST", path, {
    ...init,
    body: typeof body === "undefined" ? undefined : JSON.stringify(body),
  });
}

export function prettyBody(body: ApiBody): string {
  if (typeof body === "string") return body;

  try {
    return JSON.stringify(body, null, 2);
  } catch {
    return String(body);
  }
}

export function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function asString(v: unknown): string | null {
  return typeof v === "string" ? v : null;
}

export function extractApiError(body: unknown): string | null {
  if (typeof body === "string") {
    try {
      const parsed = JSON.parse(body) as unknown;
      if (isRecord(parsed)) {
        const detail = parsed.detail;
        if (typeof detail === "string") return detail;
        if (isRecord(detail) && typeof detail.code === "string") return detail.code;
      }
    } catch {
      // keep raw string fallback
    }
    return body;
  }

  if (isRecord(body)) {
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (isRecord(detail) && typeof detail.code === "string") return detail.code;
  }

  return null;
}
