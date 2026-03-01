import { useEffect, useState } from "react";
import EditorialRichText from "../components/EditorialRichText";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { getPublicEditorial, type PublicEditorialDetail } from "../publicEditorialApi";

export default function NewsPostPage({ slug }: { slug: string }): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [news, setNews] = useState<PublicEditorialDetail | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      const result = await getPublicEditorial("news", slug);
      if (!active) return;

      if (!result.ok) {
        if (result.status === 404) {
          setNews(null);
          setLoading(false);
          return;
        }
        setError("Der News-Artikel konnte nicht geladen werden.");
        setLoading(false);
        return;
      }

      setNews(result.body);
      setLoading(false);
    }

    void load();
    return () => {
      active = false;
    };
  }, [slug]);

  if (loading) {
    return (
      <main className="ltc-main ltc-main--narrow">
        <nav className="ltc-article-nav" aria-label="Article navigation">
          <a href="#/news" className="ltc-article-nav__link" aria-label="Zurück zur Newsliste">
            ← Zurück zu News
          </a>
        </nav>
        <p className="ltc-muted">Artikel wird geladen...</p>
      </main>
    );
  }

  if (!news && !error) {
    return (
      <main className="ltc-main ltc-main--narrow">
        <h1>Artikel nicht gefunden</h1>
        <p>Der gesuchte News-Artikel existiert nicht.</p>
        <a href="#/news" className="ltc-button ltc-button--primary">Zu News</a>
      </main>
    );
  }

  return (
    <main className="ltc-main ltc-main--narrow">
      <nav className="ltc-article-nav" aria-label="Article navigation">
        <a href="#/news" className="ltc-article-nav__link" aria-label="Zurück zur Newsliste">
          ← Zurück zu News
        </a>
      </nav>

      <article className="ltc-article" aria-label={`Nachrichtenartikel: ${news?.title ?? "Fehler"}`}>
        <h1>{news?.title ?? "News"}</h1>
        {news?.published_at ? <p className="ltc-article__meta">{new Date(news.published_at).toLocaleDateString("de-DE")}</p> : null}
        {error ? <InlineErrorBanner message={error} /> : <EditorialRichText content={news?.content_md ?? ""} />}
      </article>
    </main>
  );
}
