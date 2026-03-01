import { type CSSProperties, type ReactNode } from "react";

function Brand() {
  return (
    <a className="ltc-brand" href="#/">
      <span className="ltc-brand__mark" aria-hidden="true" />
      <span className="ltc-brand__text">
        <span className="ltc-brand__name">LIFETIMECIRCLE</span>
        <span className="ltc-brand__sub">SERVICEHEFT 4.0</span>
      </span>
    </a>
  );
}

function Topbar(props: { right?: ReactNode }) {
  return (
    <div className="ltc-topbar">
      <div className="ltc-topbar__line" aria-hidden="true" />
      <div className="ltc-container ltc-topbar__inner">
        <Brand />
        <div className="ltc-topbar__right">{props.right}</div>
      </div>
    </div>
  );
}

export function PublicSiteFooter() {
  const trustText =
    "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

  return (
    <footer id="footer" className="ltc-footer">
      <div className="ltc-container">
        <div className="ltc-footer__grid">
          <div>
            <div className="ltc-footer__title">LifeTimeCircle</div>
            <div className="ltc-muted">
              Digitales Fahrzeug-Serviceheft mit Fokus auf Dokumentation &amp; Proof: Uploads, Historie, prüfbare Nachweise.
            </div>
          </div>

          <div>
            <div className="ltc-footer__title">Links</div>
            <div className="ltc-footer__links">
              <a href="#/faq">FAQ</a>
              <a href="#/jobs">Jobs</a>
              <a href="#/blog">Blog</a>
              <a href="#/news">News</a>
            </div>
          </div>

          <div>
            <div className="ltc-footer__title">Rechtliches</div>
            <div className="ltc-footer__links">
              <a href="#/impressum">Impressum</a>
              <a href="#/datenschutz">Datenschutz</a>
              <a href="#/cookies">Cookie-Einstellungen</a>
              <a href="#/consent">Consent</a>
<<<<<<< HEAD
              <a href="#/contact">Kontakt</a>
=======
              <a href="#/contact">Contact</a>
>>>>>>> origin/main
            </div>
          </div>

          <div>
            <div className="ltc-footer__title">Trust-Ampel Hinweis</div>
            <div className="ltc-muted">{trustText}</div>
          </div>
        </div>

        <div className="ltc-footer__bottom">
          {"" + "\u00A9"} {new Date().getFullYear()} LifeTimeCircle {"" + "\u00B7"} ServiceHeft 4.0
        </div>
      </div>
    </footer>
  );
}

export function PublicSiteShell(props: { title: string; appStyle?: CSSProperties; children: ReactNode }) {
  return (
    <div className="ltc-app ltc-app--plain" style={props.appStyle}>
      <Topbar
        right={
          <div className="ltc-nav">
            <a href="#/" className="ltc-nav__a">
<<<<<<< HEAD
              Start
=======
              Home
>>>>>>> origin/main
            </a>
            <a href="#/faq" className="ltc-nav__a">
              FAQ
            </a>
            <a href="#/jobs" className="ltc-nav__a">
              Jobs
            </a>
            <a href="#/contact" className="ltc-nav__a">
<<<<<<< HEAD
              Kontakt
=======
              Contact
>>>>>>> origin/main
            </a>
            <a href="#/blog" className="ltc-nav__a">
              Blog
            </a>
            <a href="#/auth" className="ltc-pill">
              Login
            </a>
          </div>
        }
      />

      <main className="ltc-container ltc-page">
        <h1 className="ltc-h1">{props.title}</h1>
        <div className="ltc-prose">{props.children}</div>
      </main>

      <PublicSiteFooter />
    </div>
  );
}
