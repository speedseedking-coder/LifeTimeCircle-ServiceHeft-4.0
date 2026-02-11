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

export async function apiGet(path: string, init?: RequestInit): Promise<ApiResult> {
  const url = `/api${normalizePath(path)}`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json, text/plain, text/html;q=0.9, */*;q=0.8",
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
    const errorText =
      typeof body === "string"
        ? body.slice(0, 500)
        : (() => {
            try {
              return JSON.stringify(body).slice(0, 500);
            } catch {
              return "unknown_error_body";
            }
          })();

    return {
      ok: false,
      status: res.status,
      contentType,
      error: `http_${res.status}`,
      body: errorText,
    };
  }

  return { ok: true, status: res.status, contentType, body };
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
