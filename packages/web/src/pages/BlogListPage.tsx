const BLOG_POSTS = [
  {
    id: "spring-maintenance-2026",
    title: "Frühjahrsinspektion 2026: Das sollten Sie nicht vergessen",
    excerpt:
      "Die Frühjahrsinspektion ist essentiell, um Ihr Fahrzeug nach dem Winter wieder in Top-Zustand zu versetzen. Wir zeigen Ihnen, worauf Sie achten sollten.",
    date: "2026-03-01",
  },
  {
    id: "trust-ampel-guide",
    title: "So funktioniert die Trust-Ampel: Ein Leitfaden",
    excerpt:
      "Verstehen Sie die Trust-Ampel von LifeTimeCircle – wie sie funktioniert, was die Farben bedeuten und wie Sie Ihre Fahrzeugbewertung verbessern können.",
    date: "2026-02-28",
  },
  {
    id: "digital-vehicle-passport",
    title: "Digitaler Fahrzeugpass: Die Zukunft der Fahrzeugdokumentation",
    excerpt:
      "Der digitale Fahrzeugpass revolutioniert die Art, wie wir Fahrzeughistorien speichern und verwalten. Erfahren Sie, was Sie erwartet.",
    date: "2026-02-25",
  },
];

export default function BlogListPage(): JSX.Element {
  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>Blog</h1>
      <p className="ltc-helper-text">Neueste Artikel über Fahrzeugdokumentation und digitale Nachweise</p>

      <section className="ltc-section ltc-section--card">
        <ul className="ltc-list">
          {BLOG_POSTS.map((post) => (
            <li key={post.id} className="ltc-list__item">
              <a
                className="ltc-list__link"
                href={`#/blog/${encodeURIComponent(post.id)}`}
                style={{ display: "block", marginBottom: 8 }}
              >
                <strong>{post.title}</strong>
              </a>
              <p style={{ margin: "4px 0", opacity: 0.85, fontSize: "14px" }}>{post.excerpt}</p>
              <span style={{ opacity: 0.65, fontSize: "12px" }}>{new Date(post.date).toLocaleDateString("de-DE")}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
