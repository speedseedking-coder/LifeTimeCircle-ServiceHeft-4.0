import { useEffect, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { listPublicEditorial, type PublicEditorialSummary } from "../publicEditorialApi";

export default function BlogListPage(): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [posts, setPosts] = useState<PublicEditorialSummary[]>([]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      const result = await listPublicEditorial("blog");
      if (!active) return;

      if (!result.ok) {
        setError("Blog-Inhalte sind aktuell nicht verfügbar.");
        setLoading(false);
        return;
      }

      setPosts(result.body);
      setLoading(false);
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>Blog</h1>
      <p className="ltc-helper-text">Neueste Artikel über Fahrzeugdokumentation und digitale Nachweise</p>
      {error ? <InlineErrorBanner message={error} /> : null}

      <section className="ltc-section ltc-section--card" aria-label="Blogartikel">
        {loading ? <p className="ltc-muted">Blog wird geladen...</p> : null}
        {!loading && posts.length === 0 ? <p className="ltc-muted">Noch keine Blog-Beiträge veröffentlicht.</p> : null}
        <ul className="ltc-list" role="list" aria-label="Article list">
          {posts.map((post) => (
            <li key={post.slug} className="ltc-list__item ltc-article-list__item" role="listitem">
              <a
                className="ltc-list__link ltc-article-list__link"
                href={`#/blog/${encodeURIComponent(post.slug)}`}
                aria-label={`Artikel: ${post.title}`}
              >
                <strong>{post.title}</strong>
              </a>
              <p className="ltc-article-list__excerpt">{post.excerpt}</p>
              <span className="ltc-article-list__meta">
                {post.published_at ? new Date(post.published_at).toLocaleDateString("de-DE") : "Unveröffentlicht"}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
