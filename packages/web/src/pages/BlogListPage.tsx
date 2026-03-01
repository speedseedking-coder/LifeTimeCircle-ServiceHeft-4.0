const BLOG_POSTS = [
  {
    id: "spring-maintenance-2026",
<<<<<<< HEAD
    title: "Nachweise statt Behauptung: So wird Fahrzeughistorie belastbar",
    excerpt:
      "Eine belastbare Fahrzeughistorie entsteht nicht durch Stichworte, sondern durch nachvollziehbare Einträge, Belege und klare Zuordnung.",
=======
    title: "Frühjahrsinspektion 2026: Das sollten Sie nicht vergessen",
    excerpt:
      "Die Frühjahrsinspektion ist essentiell, um Ihr Fahrzeug nach dem Winter wieder in Top-Zustand zu versetzen. Wir zeigen Ihnen, worauf Sie achten sollten.",
>>>>>>> origin/main
    date: "2026-03-01",
  },
  {
    id: "trust-ampel-guide",
<<<<<<< HEAD
    title: "Trust-Ampel richtig lesen: Dokumentationsqualität statt Technikurteil",
    excerpt:
      "Die Trust-Ampel beschreibt, wie gut Historie und Nachweise dokumentiert sind. Sie ist bewusst keine technische Diagnose.",
=======
    title: "So funktioniert die Trust-Ampel: Ein Leitfaden",
    excerpt:
      "Verstehen Sie die Trust-Ampel von LifeTimeCircle – wie sie funktioniert, was die Farben bedeuten und wie Sie Ihre Fahrzeugbewertung verbessern können.",
>>>>>>> origin/main
    date: "2026-02-28",
  },
  {
    id: "digital-vehicle-passport",
<<<<<<< HEAD
    title: "Serviceeinträge sauber vorbereiten: Welche Angaben wirklich helfen",
    excerpt:
      "Datum, Typ, durchgeführt von, Kilometerstand und passender Nachweis machen aus einem Eintrag eine prüfbare Historie.",
=======
    title: "Digitaler Fahrzeugpass: Die Zukunft der Fahrzeugdokumentation",
    excerpt:
      "Der digitale Fahrzeugpass revolutioniert die Art, wie wir Fahrzeughistorien speichern und verwalten. Erfahren Sie, was Sie erwartet.",
>>>>>>> origin/main
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
