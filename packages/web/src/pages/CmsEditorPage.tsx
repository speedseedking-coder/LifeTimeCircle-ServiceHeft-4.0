import { useEffect, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import {
  createCmsDraft,
  getCmsArticle,
  listCmsArticles,
  publishCmsArticle,
  reviewCmsArticle,
  submitCmsArticle,
  type CmsArticleDetail,
  type CmsArticleSummary,
  type CmsContentType,
  updateCmsArticle,
} from "../editorialApi";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";
import { type Role } from "../lib/appGate";

type CmsActorRole = Extract<Role, "moderator" | "admin" | "superadmin">;

type DraftForm = {
  slug: string;
  title: string;
  excerpt: string;
  content_md: string;
};

const EMPTY_FORM: DraftForm = {
  slug: "",
  title: "",
  excerpt: "",
  content_md: "",
};

function contentLabel(contentType: CmsContentType): string {
  return contentType === "blog" ? "Blog" : "News";
}

function toWorkflowLabel(state: CmsArticleSummary["workflow_state"]): string {
  if (state === "draft") return "Draft";
  if (state === "in_review") return "In Review";
  return "Published";
}

function toErrorMessage(result: { status: number; error: string }): string {
  if (result.status === 0) return "Netzwerkfehler beim Laden des Editorial-Workspaces.";
  if (result.status === 400 && result.error === "invalid_slug") return "Der Slug ist ungültig. Erlaubt sind Kleinbuchstaben, Ziffern und Bindestriche.";
  if (result.status === 403 && result.error === "forbidden") return "Kein Zugriff auf diese Editorial-Aktion.";
  if (result.status === 404 && result.error === "not_found") return "Der gewählte Beitrag wurde nicht gefunden.";
  if (result.status === 409 && result.error === "slug_conflict") return "Dieser Slug ist bereits vergeben.";
  if (result.status === 409 && result.error === "published_article_read_only") return "Veröffentlichte Artikel können nur von Superadmin direkt bearbeitet werden.";
  if (result.status === 409 && result.error === "review_required") return "Vor dem Final-Publish ist ein Review durch Admin oder Superadmin erforderlich.";
  return "Die Editorial-Aktion konnte nicht ausgeführt werden.";
}

function syncForm(article: CmsArticleDetail | null, setForm: (next: DraftForm) => void, setReviewNote: (next: string) => void): void {
  if (!article) {
    setForm(EMPTY_FORM);
    setReviewNote("");
    return;
  }

  setForm({
    slug: article.slug,
    title: article.title,
    excerpt: article.excerpt,
    content_md: article.content_md,
  });
  setReviewNote(article.review_note ?? "");
}

export default function CmsEditorPage(props: { contentType: CmsContentType; actorRole: CmsActorRole }): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState("");
  const [articles, setArticles] = useState<CmsArticleSummary[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<CmsArticleDetail | null>(null);
  const [form, setForm] = useState<DraftForm>(EMPTY_FORM);
  const [reviewNote, setReviewNote] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadWorkspace(preferredArticleId?: string | null) {
    setLoading(true);
    setError("");

    const headers = authHeaders(getAuthToken());
    const listResult = await listCmsArticles(props.contentType, { headers });
    if (!listResult.ok) {
      setLoading(false);
      if (listResult.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(listResult));
      return;
    }

    const nextArticles = listResult.body;
    setArticles(nextArticles);

    const nextArticleId =
      preferredArticleId && nextArticles.some((item) => item.article_id === preferredArticleId)
        ? preferredArticleId
        : selectedArticle && nextArticles.some((item) => item.article_id === selectedArticle.article_id)
          ? selectedArticle.article_id
          : null;

    if (!nextArticleId) {
      setSelectedArticle(null);
      syncForm(null, setForm, setReviewNote);
      setLoading(false);
      return;
    }

    const detailResult = await getCmsArticle(props.contentType, nextArticleId, { headers });
    setLoading(false);

    if (!detailResult.ok) {
      if (detailResult.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(detailResult));
      return;
    }

    setSelectedArticle(detailResult.body);
    syncForm(detailResult.body, setForm, setReviewNote);
  }

  useEffect(() => {
    void loadWorkspace();
  }, [props.contentType]);

  async function openArticle(articleId: string) {
    setBusyAction(`open:${articleId}`);
    setError("");

    const detailResult = await getCmsArticle(props.contentType, articleId, {
      headers: authHeaders(getAuthToken()),
    });

    setBusyAction("");
    if (!detailResult.ok) {
      if (detailResult.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(detailResult));
      return;
    }

    setSelectedArticle(detailResult.body);
    syncForm(detailResult.body, setForm, setReviewNote);
  }

  async function runAction(
    key: string,
    action: () => Promise<{ ok: true; body: CmsArticleDetail } | { ok: false; status: number; error: string }>,
    successMessage: string,
  ) {
    setBusyAction(key);
    setError("");
    setNotice("");

    const result = await action();
    setBusyAction("");

    if (!result.ok) {
      if (result.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(toErrorMessage(result));
      return;
    }

    setNotice(successMessage);
    await loadWorkspace(result.body.article_id);
  }

  const isAdminReviewer = props.actorRole === "admin" || props.actorRole === "superadmin";
  const isSuperadmin = props.actorRole === "superadmin";
  const isPublished = selectedArticle?.workflow_state === "published";
  const previewHref =
    selectedArticle && selectedArticle.workflow_state === "published"
      ? `#/${props.contentType}/${encodeURIComponent(selectedArticle.slug)}`
      : null;

  return (
    <main className="ltc-main ltc-main--xl" data-testid={`cms-${props.contentType}-page`}>
      <section className="ltc-page-intro">
        <div className="ltc-page-intro__copy">
          <div className="ltc-page-intro__eyebrow">Editorial</div>
          <h1>{contentLabel(props.contentType)} CMS</h1>
          <p>Moderator erstellt Entwürfe, Admin reviewed, Superadmin publisht final. Keine Produkt- oder PII-Flächen außerhalb des Content-Workflows.</p>
        </div>
        <div className="ltc-page-intro__meta">
          <div className="ltc-kpi-tile">
            <div className="ltc-kpi-tile__label">Actor</div>
            <div className="ltc-kpi-tile__value">{props.actorRole}</div>
            <div className="ltc-kpi-tile__meta">Aktive Editorial-Sicht</div>
          </div>
        </div>
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}
      {notice ? (
        <section className="ltc-card ltc-card--compact ltc-section ltc-state-panel ltc-state-panel--info" role="status" aria-live="polite">
          <div className="ltc-state-panel__title">Status</div>
          <p className="ltc-state-panel__copy">{notice}</p>
        </section>
      ) : null}

      {loading ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <div className="ltc-muted">Editorial-Daten werden geladen...</div>
        </section>
      ) : (
        <div className="ltc-layout-grid ltc-layout-grid--sidebar ltc-section">
          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Queue</span>
            <div className="ltc-card__title">{contentLabel(props.contentType)} Beiträge</div>
            <div className="ltc-muted">Veröffentlichte Inhalte bleiben sichtbar. Neue Entwürfe können lokal ohne Bypass erstellt und weitergereicht werden.</div>

            <div className="ltc-admin-actions">
              <button
                type="button"
                className="ltc-btn ltc-btn--primary"
                onClick={() => {
                  setSelectedArticle(null);
                  syncForm(null, setForm, setReviewNote);
                  setNotice("");
                  setError("");
                }}
              >
                Neuer Entwurf
              </button>
            </div>

            {articles.length === 0 ? <p className="ltc-muted ltc-mt-4">Noch keine Inhalte vorhanden.</p> : null}

            <div className="ltc-admin-list">
              {articles.map((article) => (
                <article key={article.article_id} className="ltc-card ltc-card--compact ltc-card--subtle">
                  <div className="ltc-admin-head">
                    <div>
                      <div className="ltc-card__title">{article.title}</div>
                      <div className="ltc-muted">
                        <code>{article.slug}</code> · {toWorkflowLabel(article.workflow_state)}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="ltc-btn ltc-btn--ghost"
                      disabled={busyAction === `open:${article.article_id}`}
                      onClick={() => void openArticle(article.article_id)}
                    >
                      Öffnen
                    </button>
                  </div>
                  <p className="ltc-helper-text">{article.excerpt}</p>
                  <div className="ltc-meta">
                    Update {new Date(article.updated_at).toLocaleString("de-DE")}
                    {article.published_at ? ` · live ${new Date(article.published_at).toLocaleString("de-DE")}` : ""}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Editor</span>
            <div className="ltc-card__title">{selectedArticle ? "Beitrag bearbeiten" : "Neuen Entwurf anlegen"}</div>
            <div className="ltc-muted">
              Workflow-Status: <strong>{selectedArticle ? toWorkflowLabel(selectedArticle.workflow_state) : "New Draft"}</strong>
              {previewHref ? (
                <>
                  {" "}
                  · <a className="ltc-link" href={previewHref}>Public Preview</a>
                </>
              ) : null}
            </div>

            <div className="ltc-admin-form">
              <label>
                Slug
                <input
                  value={form.slug}
                  onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value.toLowerCase() }))}
                  className="ltc-form-group__input"
                  placeholder="z. B. trust-ampel-guide"
                  autoComplete="off"
                />
              </label>

              <label>
                Titel
                <input
                  value={form.title}
                  onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                  className="ltc-form-group__input"
                  placeholder="Prägnante Headline"
                  autoComplete="off"
                />
              </label>

              <label>
                Excerpt
                <textarea
                  value={form.excerpt}
                  onChange={(event) => setForm((current) => ({ ...current, excerpt: event.target.value }))}
                  className="ltc-form-group__textarea"
                  rows={4}
                  placeholder="Kurzfassung für Liste und Review."
                />
              </label>

              <label>
                Content (Markdown-light)
                <textarea
                  value={form.content_md}
                  onChange={(event) => setForm((current) => ({ ...current, content_md: event.target.value }))}
                  className="ltc-form-group__textarea"
                  rows={16}
                  placeholder="Text, Abschnitte und Listen."
                />
              </label>

              {isAdminReviewer ? (
                <label>
                  Review Note
                  <textarea
                    value={reviewNote}
                    onChange={(event) => setReviewNote(event.target.value)}
                    className="ltc-form-group__textarea"
                    rows={5}
                    placeholder="Kurzer Review-Hinweis für den Workflow."
                  />
                </label>
              ) : null}
            </div>

            <div className="ltc-admin-actions">
              <button
                type="button"
                className="ltc-btn ltc-btn--primary"
                disabled={busyAction.length > 0}
                onClick={() =>
                  void runAction(
                    selectedArticle ? "save:update" : "save:create",
                    () =>
                      selectedArticle
                        ? updateCmsArticle(props.contentType, selectedArticle.article_id, form, {
                            headers: authHeaders(getAuthToken()),
                          })
                        : createCmsDraft(props.contentType, form, { headers: authHeaders(getAuthToken()) }),
                    selectedArticle ? "Beitrag gespeichert." : "Neuer Entwurf gespeichert.",
                  )
                }
              >
                {selectedArticle ? "Speichern" : "Entwurf erstellen"}
              </button>

              {selectedArticle ? (
                <button
                  type="button"
                  className="ltc-btn ltc-btn--ghost"
                  disabled={busyAction.length > 0 || isPublished}
                  onClick={() =>
                    void runAction(
                      "submit",
                      () => submitCmsArticle(props.contentType, selectedArticle.article_id, { headers: authHeaders(getAuthToken()) }),
                      "Beitrag wurde zum Review eingereicht.",
                    )
                  }
                >
                  Review anfordern
                </button>
              ) : null}

              {isAdminReviewer && selectedArticle ? (
                <button
                  type="button"
                  className="ltc-btn ltc-btn--ghost"
                  disabled={busyAction.length > 0 || isPublished}
                  onClick={() =>
                    void runAction(
                      "review",
                      () =>
                        reviewCmsArticle(props.contentType, selectedArticle.article_id, reviewNote, {
                          headers: authHeaders(getAuthToken()),
                        }),
                      "Review gespeichert.",
                    )
                  }
                >
                  Review setzen
                </button>
              ) : null}

              {isSuperadmin && selectedArticle ? (
                <button
                  type="button"
                  className="ltc-btn ltc-btn--ghost"
                  disabled={busyAction.length > 0 || selectedArticle.workflow_state !== "in_review"}
                  onClick={() =>
                    void runAction(
                      "publish",
                      () => publishCmsArticle(selectedArticle.article_id, { headers: authHeaders(getAuthToken()) }),
                      "Beitrag wurde final veröffentlicht.",
                    )
                  }
                >
                  Final publish
                </button>
              ) : null}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
