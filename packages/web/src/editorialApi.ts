import { apiGet, apiPost, extractApiError, isRecord } from "./api";

export type CmsContentType = "blog" | "news";
export type CmsWorkflowState = "draft" | "in_review" | "published";

export type EditorialApiResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; body?: unknown; error: string };

export type CmsArticleSummary = {
  article_id: string;
  content_type: CmsContentType;
  slug: string;
  title: string;
  excerpt: string;
  workflow_state: CmsWorkflowState;
  review_note: string | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  reviewed_at: string | null;
  published_at: string | null;
};

export type CmsArticleDetail = CmsArticleSummary & {
  content_md: string;
};

function asIsoOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function mapCmsArticleSummary(body: unknown): CmsArticleSummary | null {
  if (!isRecord(body)) return null;
  if (
    typeof body.article_id !== "string" ||
    (body.content_type !== "blog" && body.content_type !== "news") ||
    typeof body.slug !== "string" ||
    typeof body.title !== "string" ||
    typeof body.excerpt !== "string" ||
    (body.workflow_state !== "draft" && body.workflow_state !== "in_review" && body.workflow_state !== "published") ||
    typeof body.created_at !== "string" ||
    typeof body.updated_at !== "string"
  ) {
    return null;
  }

  return {
    article_id: body.article_id,
    content_type: body.content_type,
    slug: body.slug,
    title: body.title,
    excerpt: body.excerpt,
    workflow_state: body.workflow_state,
    review_note: typeof body.review_note === "string" ? body.review_note : null,
    created_at: body.created_at,
    updated_at: body.updated_at,
    submitted_at: asIsoOrNull(body.submitted_at),
    reviewed_at: asIsoOrNull(body.reviewed_at),
    published_at: asIsoOrNull(body.published_at),
  };
}

function mapCmsArticleDetail(body: unknown): CmsArticleDetail | null {
  const summary = mapCmsArticleSummary(body);
  if (!summary || !isRecord(body) || typeof body.content_md !== "string") return null;
  return {
    ...summary,
    content_md: body.content_md,
  };
}

function mapSummaryList(body: unknown): CmsArticleSummary[] | null {
  if (!Array.isArray(body)) return null;
  const items: CmsArticleSummary[] = [];
  for (const item of body) {
    const mapped = mapCmsArticleSummary(item);
    if (!mapped) return null;
    items.push(mapped);
  }
  return items;
}

function toFailure<T>(status: number, body: unknown): EditorialApiResult<T> {
  return {
    ok: false,
    status,
    body,
    error: extractApiError(body) ?? `http_${status}`,
  };
}

export async function listCmsArticles(contentType: CmsContentType, init?: RequestInit): Promise<EditorialApiResult<CmsArticleSummary[]>> {
  const result = await apiGet(`/cms/${contentType}`, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapSummaryList(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function getCmsArticle(contentType: CmsContentType, articleId: string, init?: RequestInit): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiGet(`/cms/${contentType}/${encodeURIComponent(articleId)}`, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function createCmsDraft(
  contentType: CmsContentType,
  payload: { slug: string; title: string; excerpt: string; content_md: string },
  init?: RequestInit,
): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiPost(`/cms/${contentType}/drafts`, payload, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function updateCmsArticle(
  contentType: CmsContentType,
  articleId: string,
  payload: { slug: string; title: string; excerpt: string; content_md: string },
  init?: RequestInit,
): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiPost(`/cms/${contentType}/${encodeURIComponent(articleId)}`, payload, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function submitCmsArticle(
  contentType: CmsContentType,
  articleId: string,
  init?: RequestInit,
): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiPost(`/cms/${contentType}/${encodeURIComponent(articleId)}/submit`, undefined, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function reviewCmsArticle(
  contentType: CmsContentType,
  articleId: string,
  reviewNote: string,
  init?: RequestInit,
): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiPost(`/cms/review/${contentType}/${encodeURIComponent(articleId)}`, { review_note: reviewNote }, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}

export async function publishCmsArticle(articleId: string, init?: RequestInit): Promise<EditorialApiResult<CmsArticleDetail>> {
  const result = await apiPost(`/cms/publish/${encodeURIComponent(articleId)}`, undefined, init);
  if (!result.ok) return toFailure(result.status, result.body);
  const mapped = mapCmsArticleDetail(result.body);
  if (!mapped) return { ok: false, status: 500, body: result.body, error: "invalid_body" };
  return { ok: true, status: result.status, body: mapped };
}
