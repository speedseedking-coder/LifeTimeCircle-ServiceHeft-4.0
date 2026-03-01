const BLOG_CONTENT: Record<string, { title: string; date: string; content: string }> = {
  "spring-maintenance-2026": {
<<<<<<< HEAD
    title: "Nachweise statt Behauptung: So wird Fahrzeughistorie belastbar",
    date: "2026-03-01",
    content: `Eine belastbare Fahrzeughistorie beginnt nicht mit einer großen Behauptung, sondern mit einem sauberen Eintrag und einem passenden Nachweis.\n\n**Was in jeden guten Eintrag gehört:**\n- Datum der Arbeit\n- Typ des Eintrags\n- durchgeführt von\n- Kilometerstand\n- kurze, sachliche Beschreibung\n\n**Welche Nachweise den Unterschied machen:**\n- Rechnung oder Werkstattbeleg\n- Prüfbericht oder Gutachten\n- Foto der Arbeit oder des Bauteils\n- Zusatzdokumente nur dann, wenn sie zum Eintrag passen\n\nWenn Einträge und Nachweise sauber zusammengehören, wird Historie nachvollziehbar. Genau darauf baut das Service Heft 4.0 auf.`,
  },
  "trust-ampel-guide": {
    title: "Trust-Ampel richtig lesen: Dokumentationsqualität statt Technikurteil",
    date: "2026-02-28",
    content: `Die Trust-Ampel zeigt, wie gut eine Fahrzeughistorie dokumentiert und nachweisbar ist. Sie bewertet nicht, ob ein Fahrzeug technisch gut oder schlecht ist.\n\n**So lesen Sie die Anzeige richtig:**\n- GRÜN steht für gut belegte und nachvollziehbare Historie\n- GELB zeigt, dass Dokumentation vorhanden ist, aber Lücken bleiben\n- ORANGE oder ROT weisen auf geringe Nachweisqualität oder fehlende Belege hin\n\n**Was die Bewertung verbessert:**\n- Einträge vollständig anlegen\n- Nachweise direkt am passenden Eintrag hochladen\n- Unfall- und Prüfkontexte nicht weglassen\n- Dokumentation aktuell und plausibel halten\n\nDie Trust-Ampel bleibt damit ein Werkzeug für Dokumentationsqualität. Sie ersetzt keine technische Prüfung und kein Gutachten.`,
  },
  "digital-vehicle-passport": {
    title: "Serviceeinträge sauber vorbereiten: Welche Angaben wirklich helfen",
    date: "2026-02-25",
    content: `Ein Eintrag wird erst dann nützlich, wenn er für andere lesbar und prüfbar bleibt. Dafür helfen wenige Pflichtangaben mehr als viel Freitext.\n\n**Diese Felder sollten sauber gepflegt sein:**\n- Datum\n- Typ\n- durchgeführt von\n- Kilometerstand\n- kurze Bemerkung nur mit relevanten Fakten\n\n**Typische Fehler, die Trust kosten:**\n- unklare Werkstatt- oder Quellenangaben\n- fehlender Kilometerstand\n- Beleg ohne Bezug zum Eintrag\n- Fotos oder PDFs ohne erkennbaren Kontext\n\nWenn du diese Punkte konsequent pflegst, steigen Nachvollziehbarkeit, Trust-Stufe und Qualität des gesamten Verlaufs.`,
=======
    title: "Frühjahrsinspektion 2026: Das sollten Sie nicht vergessen",
    date: "2026-03-01",
    content: `Die Frühjahrsinspektion ist ein wichtiger Punkt im Wartungskalender jeden Fahrzeughalters. Nach den Wintermonaten sollten Sie Ihr Fahrzeug gründlich überprüfen.\n\n**Checkliste für die Frühjahrsinspektion:**\n- Reifen: Verschleiß prüfen, Druck kontrollieren (Winter- auf Sommerreifen wechseln)\n- Bremsanlage: Beläge inspizieren, Flüssigkeit überprüfen\n- Filter: Luft- und Pollenfilter wechseln\n- Beleuchtung: Scheinwerfer und Bremslichter testen\n- Flüssigkeiten: Motoröl, Kühlmittel, Scheibenwischflüssigkeit nachfüllen\n- Batterie: Spannung und Verschleiß testen\n- Korrosion: Fahrzeugboden und Unterboden auf Rost überprüfen\n\nDie digitale Dokumentation Ihrer Wartungen über LifeTimeCircle sorgt für Transparenz und erhöht langfristig den Wiederverkaufswert Ihres Fahrzeugs.`,
  },
  "trust-ampel-guide": {
    title: "So funktioniert die Trust-Ampel: Ein Leitfaden",
    date: "2026-02-28",
    content: `Die Trust-Ampel von LifeTimeCircle ist ein innovatives Bewertungssystem zur Visualisierung der Dokumentations- und Nachweisqualität eines Fahrzeugs.\n\n**Farbbedeutung:**\n- **GRÜN**: Umfassende Dokumentation und Nachweise, hohe Transparenz\n- **GELB**: Teilweise Dokumentation, normale Transparenz\n- **ORANGE**: Begrenzte Dokumentation, niedrigere Transparenz\n- **ROT**: Unzureichende Dokumentation oder Hinweise auf Probleme\n\n**Wie verbessern Sie Ihre Bewertung?**\n1. Laden Sie regelmäßig Wartungsbelege hoch\n2. Dokumentieren Sie alle Inspektionen und Reparaturen\n3. Fügen Sie TÜV-Berichte und technische Unterlagen hinzu\n4. Halten Sie Ihre Unfalldaten aktuell\n\nDie Trust-Ampel ist **keine Aussage über den technischen Zustand** Ihres Fahrzeugs, sondern misst ausschließlich die Qualität der verfügbaren Dokumentation und Nachweise.`,
  },
  "digital-vehicle-passport": {
    title: "Digitaler Fahrzeugpass: Die Zukunft der Fahrzeugdokumentation",
    date: "2026-02-25",
    content: `Der digitale Fahrzeugpass (Digital Vehicle Passport, DVP) ist ein EU-Standard, der ab 2027 verpflichtend wird. LifeTimeCircle bereitet Fahrzeughalter und Werkstätten auf diese Veränderung vor.\n\n**Was ist ein digitaler Fahrzeugpass?**\nEin zentrales, digitales Repository aller fahrzeugbezogenen Informationen:\n- Fahrzeugidentifikation und technische Daten\n- Wartungshistorie und Inspektionsberichte\n- Reparaturunterlagen und Teileaustausch\n- Verkehrsunfallhistorie\n- Emissionswerte und Compliance-Daten\n\n**Vorteile:**\n- Transparenz beim Fahrzeugkauf\n- Bessere Wartungsplanung\n- Erhöhte Verkehrssicherheit\n- Reduzierter Verwaltungsaufwand\n- Höherer Wiederverkaufswert\n\nLifeTimeCircle's Service-Heft-System ist bereits vollständig kompatibel mit den zukünftigen DVP-Standards.`,
>>>>>>> origin/main
  },
};

export default function BlogPostPage({ slug }: { slug: string }): JSX.Element {
  const post = BLOG_CONTENT[slug];

  if (!post) {
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

      <article className="ltc-article" aria-label={`Blogartikel: ${post.title}`}>
        <h1>{post.title}</h1>
        <p className="ltc-article__meta">{new Date(post.date).toLocaleDateString("de-DE")}</p>

        <section className="ltc-article__content">
          {post.content.split("\\n\\n").map((paragraph, index) => {
            if (paragraph.startsWith("**")) {
              return (
                <strong key={index} className="ltc-article__heading">
                  {paragraph.replace(/\*\*/g, "")}
                </strong>
              );
            }
            if (paragraph.startsWith("-")) {
              return (
                <ul key={index} className="ltc-article__list">
                  {paragraph.split("\\n").map((item, i) => (
                    <li key={i}>
                      {item.replace(/^- /, "")}
                    </li>
                  ))}
                </ul>
              );
            }
            return (
              <p key={index} className="ltc-article__paragraph">
                {paragraph}
              </p>
            );
          })}
        </section>
      </article>
    </main>
  );
}
