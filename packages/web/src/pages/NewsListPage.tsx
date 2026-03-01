const NEWS_ITEMS = [
  {
    id: "eu-digital-vehicle-passport-2027",
    title: "Produktstatus: Public-QR bleibt bewusst datenarm",
    excerpt:
      "Der öffentliche Mini-Check zeigt nur Ampel und textliche Indikatoren. Kennzahlen, Downloads und Technikdiagnosen bleiben bewusst außen vor.",
    date: "2026-03-01",
  },
  {
    id: "ltc-expands-to-fleet-management",
    title: "Produktupdate: Uploads starten weiterhin in Quarantäne",
    excerpt:
      "Nachweise werden zuerst geprüft. Erst danach sind sie im vorgesehenen Flow nutzbar. Das schützt Public- und Kernbereiche vor ungeprüften Dateien.",
    date: "2026-02-27",
  },
  {
    id: "trust-ampel-reaches-100k-vehicles",
    title: "Governance: Moderator bleibt strikt auf Blog und News begrenzt",
    excerpt:
      "Die Rollenlogik bleibt eng: Moderator bearbeitet Inhalte, aber keine Fahrzeug-, Dokument- oder Admin-Prozesse.",
    date: "2026-02-20",
  },
];

export default function NewsListPage(): JSX.Element {
  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>News</h1>
      <p className="ltc-helper-text">Aktuelle Nachrichten rund um LifeTimeCircle und digitale Fahrzeugdokumentation</p>

      <section className="ltc-section ltc-section--card" aria-label="Newsartikel">
        <ul className="ltc-list" role="list" aria-label="Article list">
          {NEWS_ITEMS.map((item) => (
            <li key={item.id} className="ltc-list__item ltc-article-list__item" role="listitem">
              <a
                className="ltc-list__link ltc-article-list__link"
                href={`#/news/${encodeURIComponent(item.id)}`}
                aria-label={`Artikel: ${item.title}`}
              >
                <strong>{item.title}</strong>
              </a>
              <p className="ltc-article-list__excerpt">{item.excerpt}</p>
              <span className="ltc-article-list__meta">{new Date(item.date).toLocaleDateString("de-DE")}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
