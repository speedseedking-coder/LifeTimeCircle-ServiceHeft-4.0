const NEWS_CONTENT: Record<string, { title: string; date: string; content: string }> = {
  "eu-digital-vehicle-passport-2027": {
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
