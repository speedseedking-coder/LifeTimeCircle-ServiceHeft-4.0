const NEWS_CONTENT: Record<string, { title: string; date: string; content: string }> = {
  "eu-digital-vehicle-passport-2027": {
<<<<<<< HEAD
    title: "Produktstatus: Public-QR bleibt bewusst datenarm",
    date: "2026-03-01",
    content: `Der Public-QR Mini-Check bleibt bewusst knapp. Er zeigt nur das, was öffentlich vertretbar und fachlich sinnvoll ist.\n\n**Was sichtbar ist:**\n- Ampel Rot, Orange, Gelb oder Grün\n- kurze textliche Hinweise zur Dokumentationsqualität\n- keine Halterdaten und keine Technikdiagnose\n\n**Was bewusst nicht sichtbar ist:**\n- keine Kennzahlen oder Prozentwerte\n- keine Dokumente oder Downloads\n- keine internen Freigaben, keine PII und keine Diagnosedaten\n\nDamit bleibt der öffentliche Einstieg nützlich, ohne in Detaildaten oder sicherheitskritische Bereiche zu kippen.`,
  },
  "ltc-expands-to-fleet-management": {
    title: "Produktupdate: Uploads starten weiterhin in Quarantäne",
    date: "2026-02-27",
    content: `Dokumente und Nachweise werden im Produktfluss nicht ungeprüft durchgereicht. Uploads starten weiterhin im Prüfpfad.\n\n**Warum dieser Schritt wichtig ist:**\n- ungeprüfte Dateien landen nicht direkt im vorgesehenen Nutzpfad\n- Freigaben bleiben an Scan- und Admin-Status gekoppelt\n- Public- und Kernansichten zeigen keine Dokumente ohne vorgesehenen Status\n\n**Was das für Nutzer bedeutet:**\n- Upload zuerst sauber zuordnen\n- Status prüfen\n- bei Bedarf im Admin- oder Dokumenten-Flow nacharbeiten\n\nDas ist kein Komfortdetail, sondern Teil der Sicherheits- und Governance-Logik des Produkts.`,
  },
  "trust-ampel-reaches-100k-vehicles": {
    title: "Governance: Moderator bleibt strikt auf Blog und News begrenzt",
    date: "2026-02-20",
    content: `Die Rollenlogik bleibt eng und absichtlich unspektakulär. Moderator ist für Inhaltsflächen da, nicht für operative Fahrzeug- oder Governance-Aktionen.\n\n**Das bedeutet konkret:**\n- Blog und News bleiben der vorgesehene Bereich für Moderation\n- Fahrzeuge, Dokumente, Export und Admin bleiben serverseitig geschützt\n- hohe Rechte und sensible Freigaben bleiben bei Admin oder Superadmin\n\n**Warum das wichtig ist:**\n- geringere Angriffsfläche\n- klare Verantwortlichkeiten\n- weniger Risiko für Fehlbedienung in sensiblen Bereichen\n\nDie Rollenwahrheit ist damit kein Nebensatz in der Doku, sondern fester Teil des Produktverhaltens.`,
=======
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
>>>>>>> origin/main
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
      <nav className="ltc-article-nav" aria-label="Article navigation">
        <a href="#/news" className="ltc-article-nav__link" aria-label="Zurück zur Newsliste">
          ← Zurück zu News
        </a>
      </nav>

      <article className="ltc-article" aria-label={`Nachrichtenartikel: ${news.title}`}>
        <h1>{news.title}</h1>
        <p className="ltc-article__meta">{new Date(news.date).toLocaleDateString("de-DE")}</p>

        <section className="ltc-article__content">
          {news.content.split("\n\n").map((paragraph, index) => {
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
                  {paragraph.split("\n").map((item, i) => (
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
