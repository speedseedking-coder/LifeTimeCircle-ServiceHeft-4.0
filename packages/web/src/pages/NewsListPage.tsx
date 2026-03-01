const NEWS_ITEMS = [
  {
    id: "eu-digital-vehicle-passport-2027",
    title: "EU-Verordnung: Digitaler Fahrzeugpass ab 2027 verpflichtend",
    excerpt:
      "Die Europäische Union hat beschlossen, dass der digitale Fahrzeugpass (DVP) ab 2027 für alle Neufahrzeuge obligatorisch wird. LifeTimeCircle ist bereit.",
    date: "2026-03-01",
  },
  {
    id: "ltc-expands-to-fleet-management",
    title: "LifeTimeCircle erweitert Angebot auf professionelle Flottenmanagement",
    excerpt:
      "Ab Q2 2026 ist LifeTimeCircle auch für Fuhrpark-Manager und Autovermietungen verfügbar. Neue B2B-Features und Reporting-Tools.",
    date: "2026-02-27",
  },
  {
    id: "trust-ampel-reaches-100k-vehicles",
    title: "Meilenstein: 100.000 Fahrzeuge auf LifeTimeCircle dokumentiert",
    excerpt:
      "Die LifeTimeCircle-Community hat eine beeindruckende Marke erreicht! Mehr als 100.000 Fahrzeuge sind jetzt vollständig digital erfasst.",
    date: "2026-02-20",
  },
];

export default function NewsListPage(): JSX.Element {
  return (
    <main className="ltc-main ltc-main--narrow">
      <h1>News</h1>
      <p className="ltc-helper-text">Aktuelle Nachrichten rund um LifeTimeCircle und digitale Fahrzeugdokumentation</p>

      <section className="ltc-section ltc-section--card">
        <ul className="ltc-list">
          {NEWS_ITEMS.map((item) => (
            <li key={item.id} className="ltc-list__item">
              <a
                className="ltc-list__link"
                href={`#/news/${encodeURIComponent(item.id)}`}
                style={{ display: "block", marginBottom: 8 }}
              >
                <strong>{item.title}</strong>
              </a>
              <p style={{ margin: "4px 0", opacity: 0.85, fontSize: "14px" }}>{item.excerpt}</p>
              <span style={{ opacity: 0.65, fontSize: "12px" }}>{new Date(item.date).toLocaleDateString("de-DE")}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
