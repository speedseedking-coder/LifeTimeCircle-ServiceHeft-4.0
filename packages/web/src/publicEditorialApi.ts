import { apiGet, extractApiError, isRecord } from "./api";

export type PublicEditorialContentType = "blog" | "news";

export type PublicEditorialSummary = {
  slug: string;
  title: string;
  excerpt: string;
  published_at: string | null;
};

export type PublicEditorialDetail = PublicEditorialSummary & {
  content_md: string;
};

export type PublicEditorialResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; body?: unknown; error: string };

function asIsoOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function mapSummary(body: unknown): PublicEditorialSummary | null {
  if (!isRecord(body)) return null;
  if (typeof body.slug !== "string" || typeof body.title !== "string" || typeof body.excerpt !== "string") {
    return null;
  }

  return {
    slug: body.slug,
    title: body.title,
    excerpt: body.excerpt,
    published_at: asIsoOrNull(body.published_at),
  };
}

function mapDetail(body: unknown): PublicEditorialDetail | null {
  const summary = mapSummary(body);
  if (!summary || !isRecord(body) || typeof body.content_md !== "string") return null;
  return {
    ...summary,
    content_md: body.content_md,
  };
}

function mapSummaryList(body: unknown): PublicEditorialSummary[] | null {
  if (!Array.isArray(body)) return null;
  const items: PublicEditorialSummary[] = [];
  for (const item of body) {
    const mapped = mapSummary(item);
    if (!mapped) return null;
    items.push(mapped);
  }
  return items;
}

function toFailure<T>(status: number, body: unknown): PublicEditorialResult<T> {
  return {
    ok: false,
    status,
    body,
    error: extractApiError(body) ?? `http_${status}`,
  };
}

export async function listPublicEditorial(
  contentType: PublicEditorialContentType,
  init?: RequestInit,
): Promise<PublicEditorialResult<PublicEditorialSummary[]>> {
  const result = await apiGet(`/${contentType}`, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapSummaryList(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function getPublicEditorial(
  contentType: PublicEditorialContentType,
  slug: string,
  init?: RequestInit,
): Promise<PublicEditorialResult<PublicEditorialDetail>> {
  const result = await apiGet(`/${contentType}/${encodeURIComponent(slug)}`, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}
