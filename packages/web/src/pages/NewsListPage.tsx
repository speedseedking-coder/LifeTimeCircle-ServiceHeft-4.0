import { useEffect, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { listPublicEditorial, type PublicEditorialSummary } from "../publicEditorialApi";

export default function NewsListPage(): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [items, setItems] = useState<PublicEditorialSummary[]>([]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      const result = await listPublicEditorial("news");
      if (!active) return;

      if (!result.ok) {
        setError("News-Inhalte sind aktuell nicht verfügbar.");
        setLoading(false);
        return;
      }

      setItems(result.body);
      setLoading(false);
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>News</h1>
      <p className="ltc-helper-text">Aktuelle Nachrichten rund um LifeTimeCircle und digitale Fahrzeugdokumentation</p>
      {error ? <InlineErrorBanner message={error} /> : null}

      <section className="ltc-section ltc-section--card" aria-label="Newsartikel">
        {loading ? <p className="ltc-muted">News werden geladen...</p> : null}
        {!loading && items.length === 0 ? <p className="ltc-muted">Noch keine News veröffentlicht.</p> : null}
        <ul className="ltc-list" role="list" aria-label="Article list">
          {items.map((item) => (
            <li key={item.slug} className="ltc-list__item ltc-article-list__item" role="listitem">
              <a
                className="ltc-list__link ltc-article-list__link"
                href={`#/news/${encodeURIComponent(item.slug)}`}
                aria-label={`Artikel: ${item.title}`}
              >
                <strong>{item.title}</strong>
              </a>
              <p className="ltc-article-list__excerpt">{item.excerpt}</p>
              <span className="ltc-article-list__meta">
                {item.published_at ? new Date(item.published_at).toLocaleDateString("de-DE") : "Unveröffentlicht"}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
