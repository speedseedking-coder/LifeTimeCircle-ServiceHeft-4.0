import { useEffect, useState } from "react";
import EditorialRichText from "../components/EditorialRichText";
import InlineErrorBanner from "../components/InlineErrorBanner";
import { getPublicEditorial, type PublicEditorialDetail } from "../publicEditorialApi";

export default function BlogPostPage({ slug }: { slug: string }): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [post, setPost] = useState<PublicEditorialDetail | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      const result = await getPublicEditorial("blog", slug);
      if (!active) return;

      if (!result.ok) {
        if (result.status === 404) {
          setPost(null);
          setLoading(false);
          return;
        }
        setError("Der Blog-Artikel konnte nicht geladen werden.");
        setLoading(false);
        return;
      }

      setPost(result.body);
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
          <a href="#/blog" className="ltc-article-nav__link" aria-label="Zurück zur Blogliste">
            ← Zurück zum Blog
          </a>
        </nav>
        <p className="ltc-muted">Artikel wird geladen...</p>
      </main>
    );
  }

  if (!post && !error) {
    return (
      <main className="ltc-main ltc-main--narrow">
        <h1>Artikel nicht gefunden</h1>
        <p>Der gesuchte Blog-Artikel existiert nicht.</p>
        <a href="#/blog" className="ltc-button ltc-button--primary">Zum Blog</a>
      </main>
    );
  }

  return (
    <main className="ltc-main ltc-main--narrow">
      <nav className="ltc-article-nav" aria-label="Article navigation">
        <a href="#/blog" className="ltc-article-nav__link" aria-label="Zurück zur Blogliste">
          ← Zurück zum Blog
        </a>
      </nav>

      <article className="ltc-article" aria-label={`Blogartikel: ${post?.title ?? "Fehler"}`}>
        <h1>{post?.title ?? "Blog"}</h1>
        {post?.published_at ? <p className="ltc-article__meta">{new Date(post.published_at).toLocaleDateString("de-DE")}</p> : null}
        {error ? <InlineErrorBanner message={error} /> : <EditorialRichText content={post?.content_md ?? ""} />}
      </article>
    </main>
  );
}
