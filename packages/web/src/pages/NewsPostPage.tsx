const NEWS_CONTENT: Record<string, { title: string; date: string; content: string }> = {
  "eu-digital-vehicle-passport-2027": {
    title: "EU-Verordnung: Digitaler Fahrzeugpass ab 2027 verpflichtend",
    date: "2026-03-01",
    content: `Die Europäische Kommission hat ein Gesetzespaket verabschiedet, das den Digitalen Fahrzeugpass (DVP) ab 2027 für alle Neufahrzeuge verbindlich macht.

**Was ändert sich?**
Alle Neufahrzeuge müssen ab Januar 2027 mit einem digitalen Fahrzeugpass ausgestattet sein. Dieser ersetzt nicht den physischen Fahrzeugbrief, sondern ergänzt ihn um digitale Funktionen.

**Implementierung bei LifeTimeCircle**
Unser Service-Heft-System ist vollständig vorbereitet für die DVP-Integration:
- Automatische Erfassung aller relevanten Fahrzeugdaten
- Nahtlose Übergabe an den EU-Standard
- Blockchain-basierte Datensicherheit
- Vollständige Nachverfolgbarkeit von Wartungen und Reparaturen

**Für wen ist das wichtig?**
- Fahrzeughalter: Transparenz und höherer Wiederverkaufswert
- Werkstätten: Digitale Dokumentation wird Pflicht
- Versicherungen: Bessere Risikobewertung durch Vergangenheitsdaten
- Käufer: Vollständigere Fahrzeughistorien`,
  },
  "ltc-expands-to-fleet-management": {
    title: "LifeTimeCircle erweitert Angebot auf professionelle Flottenmanagement",
    date: "2026-02-27",
    content: `LifeTimeCircle kündigt die Erweiterung seiner Plattform an: Ab Q2 2026 ist ein spezialisiertes Flottenmanagement-Modul für professionelle Fahrzeughalter verfügbar.

**Neue B2B-Features**
- Zentrale Verwaltung bis zu 1000+ Fahrzeuge
- Automatische Wartungsplanung und Benachrichtigungen
- Aggregierte Reporting und Compliance-Übersicht
- Rollenbasierter Zugang für Flottenmanager und Mechaniker
- Export-Funktionen für Audits und Zertifizierungen

**Erste Partner**
Bereits die ersten Autovermietungen und Fuhrpark-Manager sind in Beta-Testing eingebunden. Die offizielle Markteinführung erfolgt im Juni 2026.

**Pricing**
Flottenmanagement-Modul: 5€ pro Fahrzeug/Monat, mit Rabatten je nach Flottengröße.`,
  },
  "trust-ampel-reaches-100k-vehicles": {
    title: "Meilenstein: 100.000 Fahrzeuge auf LifeTimeCircle dokumentiert",
    date: "2026-02-20",
    content: `Die LifeTimeCircle-Community gratuliert sich selbst: Gestern hat die Plattform die Marke von 100.000 vollständig dokumentierten Fahrzeugen erreicht!

**Highlights des Meilensteins**
- 100.000 Fahrzeuge mit durchschnittlich 15+ Dokumentationen pro Fahrzeug
- 50.000+ aktive Nutzer in Deutschland und Österreich
- 500+ registrierte Werkstätten
- Über 1 Million Befunde und Inspektionsberichte

**Was bedeutet das?**
Dieser massive Datenschatz ermöglicht es uns, die Quality-Focus und Maintenance-Patterns zu verfeinern. Die Trust-Ampel-Algorithmen werden mit echten Daten trainiert und liefern immer bessere Prognosen.

**Danksagung**
Wir danken all unseren Partnern, Werkstätten und vor allem den Fahrzeughaltern für das Vertrauen und die ständige Unterstützung. Gemeinsam machen wir die Fahrzeugdokumentation transparenter und sicherer.`,
  },
};

export default function NewsPostPage({ slug }: { slug: string }): JSX.Element {
  const news = NEWS_CONTENT[slug];

  if (!news) {
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
      <a href="#/news" style={{ textDecoration: "none", color: "var(--ltc-color-text-secondary)" }} aria-label="Zurück zur Nachrichtenlista">← Zurück zu News</a>

      <article style={{ marginTop: 20 }} aria-label={`Nachrichtenartikel: ${news.title}`}>
        <h1>{news.title}</h1>
        <p style={{ fontSize: "14px", opacity: 0.75, marginTop: 8 }}>{new Date(news.date).toLocaleDateString("de-DE")}</p>

        <section style={{ marginTop: 24, lineHeight: 1.6, color: "var(--ltc-color-text-primary)" }}>
          {news.content.split("\n\n").map((paragraph, index) => {
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
                  {paragraph.split("\n").map((item, i) => (
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
