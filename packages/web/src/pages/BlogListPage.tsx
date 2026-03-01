const BLOG_POSTS = [
  {
    id: "spring-maintenance-2026",
    title: "Nachweise statt Behauptung: So wird Fahrzeughistorie belastbar",
    excerpt:
      "Eine belastbare Fahrzeughistorie entsteht nicht durch Stichworte, sondern durch nachvollziehbare Einträge, Belege und klare Zuordnung.",
    date: "2026-03-01",
  },
  {
    id: "trust-ampel-guide",
    title: "Trust-Ampel richtig lesen: Dokumentationsqualität statt Technikurteil",
    excerpt:
      "Die Trust-Ampel beschreibt, wie gut Historie und Nachweise dokumentiert sind. Sie ist bewusst keine technische Diagnose.",
    date: "2026-02-28",
  },
  {
    id: "digital-vehicle-passport",
    title: "Serviceeinträge sauber vorbereiten: Welche Angaben wirklich helfen",
    excerpt:
      "Datum, Typ, durchgeführt von, Kilometerstand und passender Nachweis machen aus einem Eintrag eine prüfbare Historie.",
    date: "2026-02-25",
  },
];

export default function BlogListPage(): JSX.Element {
  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>Blog</h1>
      <p className="ltc-helper-text">Neueste Artikel über Fahrzeugdokumentation und digitale Nachweise</p>

      <section className="ltc-section ltc-section--card" aria-label="Blogartikel">
        <ul className="ltc-list" role="list" aria-label="Article list">
          {BLOG_POSTS.map((post) => (
            <li key={post.id} className="ltc-list__item ltc-article-list__item" role="listitem">
              <a
                className="ltc-list__link ltc-article-list__link"
                href={`#/blog/${encodeURIComponent(post.id)}`}
                aria-label={`Artikel: ${post.title}`}
              >
                <strong>{post.title}</strong>
              </a>
              <p className="ltc-article-list__excerpt">{post.excerpt}</p>
              <span className="ltc-article-list__meta">{new Date(post.date).toLocaleDateString("de-DE")}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
