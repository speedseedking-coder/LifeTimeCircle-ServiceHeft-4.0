const BLOG_CONTENT: Record<string, { title: string; date: string; content: string }> = {
  "spring-maintenance-2026": {
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
      <a href="#/blog" style={{ textDecoration: "none", color: "var(--ltc-color-text-secondary)" }}>← Zurück zum Blog</a>

      <article style={{ marginTop: 20 }}>
        <h1>{post.title}</h1>
        <p style={{ fontSize: "14px", opacity: 0.75, marginTop: 8 }}>{new Date(post.date).toLocaleDateString("de-DE")}</p>

        <section style={{ marginTop: 24, lineHeight: 1.6, color: "var(--ltc-color-text-primary)" }}>
          {post.content.split("\\n\\n").map((paragraph, index) => {
            if (paragraph.startsWith("**")) {
              return (
                <strong key={index} style={{ display: "block", marginTop: 12, marginBottom: 8 }}>
                  {paragraph.replace(/\*\*/g, "")}
                </strong>
              );
            }
            if (paragraph.startsWith("-")) {
              return (
                <ul key={index} style={{ marginTop: 8, marginLeft: 20, opacity: 0.9 }}>
                  {paragraph.split("\\n").map((item, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>
                      {item.replace(/^- /, "")}
                    </li>
                  ))}
                </ul>
              );
            }
            return (
              <p key={index} style={{ marginTop: 12 }}>
                {paragraph}
              </p>
            );
          })}
        </section>
      </article>
    </main>
  );
}
