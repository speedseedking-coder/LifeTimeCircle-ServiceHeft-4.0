// packages/web/src/App.tsx
import { useEffect, useMemo, useState, type CSSProperties, type FormEvent, type ReactNode } from "react";
import { apiGet, asString, isRecord, prettyBody } from "./api";

import { PublicQrPage } from "./pages/PublicQrPage";

import AuthPage from "./pages/AuthPage";
import ConsentPage from "./pages/ConsentPage";
import VehiclesPage from "./pages/VehiclesPage";
import VehicleDetailPage from "./pages/VehicleDetailPage";
import DocumentsPage from "./pages/DocumentsPage";
import OnboardingWizardPage from "./pages/OnboardingWizardPage";

/**
 * LifeTimeCircle – ServiceHeft 4.0:
 * - Digitales Nachweis- & Dokumentationssystem (Proof statt Behauptung)
 * - Fokus: Uploads, Historie, prüfbare Belege / Audit-Trail
 * - Public/QR: datenarm, schnelle Checks / Reports
 * - Trust-Ampel bewertet ausschließlich Dokumentations- & Nachweisqualität (kein technischer Zustand)
 */

type Route =
  | { kind: "home" }
  | { kind: "debugPublicSite" }
  | { kind: "faq" }
  | { kind: "cookies" }
  | { kind: "jobs" }
  | { kind: "impressum" }
  | { kind: "datenschutz" }
  | { kind: "blogList" }
  | { kind: "blogPost"; slug: string }
  | { kind: "newsList" }
  | { kind: "newsPost"; slug: string }
  | { kind: "publicQr"; vehicleId: string }
  | { kind: "auth" }
  | { kind: "consent" }
  | { kind: "vehicles" }
  | { kind: "vehicleDetail"; vehicleId: string }
  | { kind: "documents" }
  | { kind: "onboarding" };

function parseHash(): Route {
  const raw = (window.location.hash || "").replace(/^#\/?/, "");
  const parts = raw.split("/").filter(Boolean);

  if (parts.length === 0) return { kind: "home" };

  // Legacy: #/public/site -> soll NICHT mehr angezeigt werden (Home)
  if (parts[0] === "public" && parts[1] === "site") return { kind: "home" };

  // Public QR (hash)
  if (parts[0] === "qr" && parts[1]) return { kind: "publicQr", vehicleId: parts[1] };
  if (parts[0] === "public" && parts[1] === "qr" && parts[2]) return { kind: "publicQr", vehicleId: parts[2] };

  // Debug: #/debug/public-site
  if (parts[0] === "debug" && parts[1] === "public-site") return { kind: "debugPublicSite" };

  // Static / Legal
  if (parts[0] === "faq") return { kind: "faq" };
  if (parts[0] === "cookies") return { kind: "cookies" };
  if (parts[0] === "jobs") return { kind: "jobs" };
  if (parts[0] === "impressum") return { kind: "impressum" };
  if (parts[0] === "datenschutz") return { kind: "datenschutz" };

  // Public content
  if (parts[0] === "blog" && parts.length === 1) return { kind: "blogList" };
  if (parts[0] === "blog" && parts[1]) return { kind: "blogPost", slug: parts[1] };
  if (parts[0] === "news" && parts.length === 1) return { kind: "newsList" };
  if (parts[0] === "news" && parts[1]) return { kind: "newsPost", slug: parts[1] };

  // app pages (hash-based)
  if (parts[0] === "auth") return { kind: "auth" };
  if (parts[0] === "consent") return { kind: "consent" };
  if (parts[0] === "vehicles" && parts.length === 1) return { kind: "vehicles" };
  if (parts[0] === "vehicles" && parts[1]) return { kind: "vehicleDetail", vehicleId: parts[1] };
  if (parts[0] === "documents") return { kind: "documents" };
  if (parts[0] === "onboarding") return { kind: "onboarding" };

  return { kind: "home" };
}

function scrollToId(id: string) {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

/** ---------------------------
 * Hintergrund-Mapping (alle Seiten)
 * --------------------------- */
type BgCfg = {
  url: string;
  opacity: number; // 0..1
  size?: string; // CSS background-size
  position?: string; // CSS background-position
};

const BG = {
  rechnungspruefer: "/images/rechnungspruefer.png",
  service2: "/images/service2.png",
  serviceheft: "/images/serviceheft.png",
  termsFaq: "/images/terms_faq.png",
  blog: "/images/Blog.png",
  cookies: "/images/cookies.png",
  consent: "/images/daten_zustim.png",
  datenschutz: "/images/datenschutz.png",
  frontpage2: "/images/frontpage_LiftimeCicrcle_2.png",
  galerie: "/images/galerie.png",
  jobs: "/images/jobs.png",
  news: "/images/news.png",
} as const;

function getBgForRoute(route: Route): BgCfg | null {
  switch (route.kind) {
    case "home":
      return null;

    case "faq":
      return { url: BG.termsFaq, opacity: 0.28, size: "contain", position: "center top" };
    case "cookies":
      return { url: BG.cookies, opacity: 0.28, size: "contain", position: "center top" };
    case "jobs":
      return { url: BG.jobs, opacity: 0.28, size: "contain", position: "center top" };
    case "impressum":
      return { url: BG.termsFaq, opacity: 0.24, size: "contain", position: "center top" };
    case "datenschutz":
      return { url: BG.datenschutz, opacity: 0.28, size: "contain", position: "center top" };

    case "blogList":
    case "blogPost":
      return { url: BG.blog, opacity: 0.22, size: "cover", position: "center" };

    case "newsList":
    case "newsPost":
      return { url: BG.news, opacity: 0.22, size: "cover", position: "center" };

    case "publicQr":
      return { url: BG.serviceheft, opacity: 0.22, size: "cover", position: "center" };

    case "auth":
      return { url: BG.frontpage2, opacity: 0.26, size: "contain", position: "center top" };

    case "consent":
      return { url: BG.consent, opacity: 0.26, size: "contain", position: "center top" };

    case "vehicles":
      return { url: BG.service2, opacity: 0.22, size: "cover", position: "center" };

    case "vehicleDetail":
      return { url: BG.serviceheft, opacity: 0.22, size: "cover", position: "center" };

    case "documents":
      return { url: BG.rechnungspruefer, opacity: 0.2, size: "cover", position: "center" };

    case "onboarding":
      return { url: BG.service2, opacity: 0.2, size: "cover", position: "center" };

    case "debugPublicSite":
      return { url: BG.frontpage2, opacity: 0.14, size: "cover", position: "center" };
  }
}

function bgStyle(bg: BgCfg | null): CSSProperties {
  if (!bg) {
    return {
      ["--ltc-bg" as any]: "none",
      ["--ltc-bg-op" as any]: "0",
      ["--ltc-bg-size" as any]: "cover",
      ["--ltc-bg-pos" as any]: "center",
    };
  }
  return {
    ["--ltc-bg" as any]: `url("${bg.url}")`,
    ["--ltc-bg-op" as any]: String(bg.opacity),
    ["--ltc-bg-size" as any]: bg.size ?? "cover",
    ["--ltc-bg-pos" as any]: bg.position ?? "center",
  };
}

/** ---------------------------
 * Cookies (Banner + Settings)
 * --------------------------- */
type CookiePrefs = {
  necessary: true;
  analytics: boolean;
  marketing: boolean;
  savedAtIso: string;
};
const COOKIE_KEY = "ltc_cookie_prefs_v1";

function loadCookiePrefs(): CookiePrefs | null {
  try {
    const raw = localStorage.getItem(COOKIE_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw) as Partial<CookiePrefs>;
    if (p.necessary !== true) return null;
    if (typeof p.analytics !== "boolean") return null;
    if (typeof p.marketing !== "boolean") return null;
    if (typeof p.savedAtIso !== "string") return null;
    return p as CookiePrefs;
  } catch {
    return null;
  }
}

function saveCookiePrefs(next: Omit<CookiePrefs, "savedAtIso">) {
  const obj: CookiePrefs = { ...next, savedAtIso: new Date().toISOString() };
  localStorage.setItem(COOKIE_KEY, JSON.stringify(obj));
  return obj;
}

function CookieBanner(props: { onOpenSettings: () => void }) {
  const [prefs, setPrefs] = useState<CookiePrefs | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setPrefs(loadCookiePrefs());
  }, []);

  if (!mounted) return null;
  if (prefs) return null;

  return (
    <div className="ltc-cookie">
      <div className="ltc-cookie__title">Cookies &amp; lokale Speicherung</div>
      <div className="ltc-cookie__text">
        Notwendig ist immer aktiv (z. B. Session/Flow). Optional kannst du Analytics aktivieren. Anpassen jederzeit unter{" "}
        <a href="#/cookies">Cookie-Einstellungen</a>.
      </div>
      <div className="ltc-cookie__actions">
        <button
          type="button"
          className="ltc-btn ltc-btn--ghost"
          onClick={() => {
            const p = saveCookiePrefs({ necessary: true, analytics: false, marketing: false });
            setPrefs(p);
          }}
        >
          Nur notwendig
        </button>
        <button
          type="button"
          className="ltc-btn ltc-btn--primary"
          onClick={() => {
            const p = saveCookiePrefs({ necessary: true, analytics: true, marketing: false });
            setPrefs(p);
          }}
        >
          Akzeptieren
        </button>
        <button type="button" className="ltc-btn ltc-btn--soft" onClick={props.onOpenSettings}>
          Einstellungen
        </button>
      </div>
    </div>
  );
}

function CookieSettingsCard(props: { onSaved?: () => void }) {
  const [prefs, setPrefs] = useState<CookiePrefs>(() => {
    return (
      loadCookiePrefs() ?? {
        necessary: true,
        analytics: false,
        marketing: false,
        savedAtIso: new Date(0).toISOString(),
      }
    );
  });

  return (
    <div className="ltc-card">
      <div className="ltc-card__title">Cookie-Einstellungen</div>
      <div className="ltc-muted">Notwendig ist immer aktiv. Analytics ist optional. Marketing/Tracking ist deaktiviert.</div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div>
          <div className="ltc-strong">Notwendig</div>
          <div className="ltc-muted">Sitzung, Sicherheit, grundlegende Funktionen</div>
        </div>
        <input type="checkbox" checked disabled className="ltc-check" />
      </div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div>
          <div className="ltc-strong">Analytics (optional)</div>
          <div className="ltc-muted">anonymisierte Nutzungsstatistik zur Verbesserung</div>
        </div>
        <input
          type="checkbox"
          checked={prefs.analytics}
          onChange={(e) => setPrefs((p) => ({ ...p, analytics: e.target.checked }))}
          className="ltc-check"
        />
      </div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div>
          <div className="ltc-strong">Marketing/Tracking</div>
          <div className="ltc-muted">derzeit nicht verwendet</div>
        </div>
        <input type="checkbox" checked={prefs.marketing} disabled className="ltc-check" />
      </div>

      <div className="ltc-actions">
        <button
          type="button"
          className="ltc-btn ltc-btn--primary"
          onClick={() => {
            saveCookiePrefs({ necessary: true, analytics: prefs.analytics, marketing: false });
            props.onSaved?.();
          }}
        >
          Speichern
        </button>

        <button
          type="button"
          className="ltc-btn ltc-btn--ghost"
          onClick={() => {
            const p = saveCookiePrefs({ necessary: true, analytics: false, marketing: false });
            setPrefs(p);
            props.onSaved?.();
          }}
        >
          Nur notwendig
        </button>
      </div>

      <div className="ltc-meta">
        Gespeichert in <code>localStorage</code> unter <code>{COOKIE_KEY}</code>.
      </div>
    </div>
  );
}

/** ---------------------------
 * Icons (inline, kein Lib)
 * --------------------------- */
function IconShield(props: { className?: string }) {
  return (
    <svg className={props.className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2l7 4v6c0 5-3 9-7 10-4-1-7-5-7-10V6l7-4z" stroke="currentColor" strokeWidth="1.6" opacity="0.9" />
      <path
        d="M9.5 12l1.8 1.8L15.8 9.3"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconCheck(props: { className?: string }) {
  return (
    <svg className={props.className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M20 12a8 8 0 11-16 0 8 8 0 0116 0z" stroke="currentColor" strokeWidth="1.6" opacity="0.9" />
      <path
        d="M7.6 12.3l2.6 2.6L16.6 8.6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconQr(props: { className?: string }) {
  return (
    <svg className={props.className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 4h6v6H4V4z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M14 4h6v6h-6V4z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 14h6v6H4v-6z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M14 14h3v3h-3v-3z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M18 18h2v2h-2v-2z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M17 17h1v1h-1v-1z" fill="currentColor" />
    </svg>
  );
}

/** ---------------------------
 * Layout Helpers
 * --------------------------- */
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

function Footer() {
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
            </div>
          </div>

          <div>
            <div className="ltc-footer__title">Trust-Ampel Hinweis</div>
            <div className="ltc-muted">{trustText}</div>
          </div>
        </div>

        <div className="ltc-footer__bottom">{"" + "\u00A9"} {new Date().getFullYear()} LifeTimeCircle {"" + "\u00B7"} ServiceHeft 4.0</div>
      </div>
    </footer>
  );
}

function StaticShell(props: { title: string; bg?: BgCfg | null; children: ReactNode }) {
  return (
    <div className="ltc-app ltc-app--plain" style={bgStyle(props.bg ?? null)}>
      <Topbar
        right={
          <div className="ltc-nav">
            <a href="#/" className="ltc-nav__a">
              Home
            </a>
            <a href="#/faq" className="ltc-nav__a">
              FAQ
            </a>
            <a href="#/jobs" className="ltc-nav__a">
              Jobs
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

      <div className="ltc-container ltc-page">
        <h1 className="ltc-h1">{props.title}</h1>
        <div className="ltc-prose">{props.children}</div>
      </div>

      <Footer />
    </div>
  );
}

/** ---------------------------
 * API Debug / Lists
 * --------------------------- */
function Card(props: { title: string; children: ReactNode }) {
  return (
    <section className="ltc-card">
      <div className="ltc-card__title">{props.title}</div>
      {props.children}
    </section>
  );
}

function ApiBox(props: { path: string; title: string }) {
  const [state, setState] = useState<{ loading: boolean; text: string; status?: number }>({ loading: true, text: "" });

  useEffect(() => {
    let alive = true;
    setState({ loading: true, text: "" });

    apiGet(props.path).then((r) => {
      if (!alive) return;

      if (!r.ok) {
        setState({
          loading: false,
          text: `${r.error}\n${typeof r.body === "string" ? r.body : ""}`.trim(),
          status: r.status,
        });
        return;
      }

      setState({ loading: false, text: prettyBody(r.body), status: r.status });
    });

    return () => {
      alive = false;
    };
  }, [props.path]);

  return (
    <Card title={props.title}>
      <div className="ltc-meta">
        GET <code>{`/api${props.path.startsWith("/") ? props.path : `/${props.path}`}`}</code>
        {typeof state.status === "number" ? ` → ${state.status}` : ""}
      </div>

      {state.loading ? <div className="ltc-muted">Lädt…</div> : <pre className="ltc-pre">{state.text}</pre>}
    </Card>
  );
}

function ItemsList(props: { title: string; path: string; kind: "blog" | "news" }) {
  const [state, setState] = useState<{
    loading: boolean;
    error?: string;
    status?: number;
    items?: Array<{ slug: string; title: string }>;
    raw?: string;
  }>({ loading: true });

  useEffect(() => {
    let alive = true;
    setState({ loading: true });

    apiGet(props.path).then((r) => {
      if (!alive) return;

      if (!r.ok) {
        setState({ loading: false, status: r.status, error: `${r.error}${r.body ? `: ${String(r.body)}` : ""}` });
        return;
      }

      const body = r.body;

      if (Array.isArray(body)) {
        const mapped = body
          .map((x) => {
            if (!isRecord(x)) return null;
            const slug = asString(x.slug) ?? asString(x.id) ?? null;
            const title = asString(x.title) ?? asString(x.name) ?? slug;
            if (!slug || !title) return null;
            return { slug, title };
          })
          .filter(Boolean) as Array<{ slug: string; title: string }>;

        if (mapped.length > 0) {
          setState({ loading: false, status: r.status, items: mapped });
          return;
        }
      }

      setState({ loading: false, status: r.status, raw: prettyBody(body) });
    });

    return () => {
      alive = false;
    };
  }, [props.path]);

  return (
    <Card title={props.title}>
      <div className="ltc-meta">
        GET <code>{`/api${props.path.startsWith("/") ? props.path : `/${props.path}`}`}</code>
        {typeof state.status === "number" ? ` → ${state.status}` : ""}
      </div>

      {state.loading ? (
        <div className="ltc-muted">Lädt…</div>
      ) : state.error ? (
        <pre className="ltc-pre">{state.error}</pre>
      ) : state.items ? (
        <ul className="ltc-list">
          {state.items.map((it) => (
            <li key={it.slug}>
              <a className="ltc-link" href={`#/${props.kind}/${encodeURIComponent(it.slug)}`}>
                {it.title}
              </a>{" "}
              <span className="ltc-muted">({it.slug})</span>
            </li>
          ))}
        </ul>
      ) : (
        <pre className="ltc-pre">{state.raw ?? ""}</pre>
      )}
    </Card>
  );
}

function PostView(props: { title: string; path: string; backHref: string; backLabel: string }) {
  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <a className="ltc-link" href={props.backHref}>
          ← {props.backLabel}
        </a>
      </div>
      <ApiBox path={props.path} title={props.title} />
    </>
  );
}

/** ---------------------------
 * Modal
 * --------------------------- */
function Modal(props: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="ltc-modal" onClick={props.onClose} role="dialog" aria-modal="true">
      <div className="ltc-modal__card" onClick={(e) => e.stopPropagation()}>
        <div className="ltc-modal__head">
          <div className="ltc-strong">{props.title}</div>
          <button type="button" className="ltc-btn ltc-btn--ghost" onClick={props.onClose}>
            Schließen
          </button>
        </div>
        <div className="ltc-modal__body">{props.children}</div>
      </div>
    </div>
  );
}

/** ---------------------------
 * Frontpage – NEU (Proportionen wie Beispiel: Hero-Banner + Phone/QR Mock, danach Cards/Showroom/Bands)
 * --------------------------- */
function FrontPage() {
  const [email, setEmail] = useState("");
  const [cookieModalOpen, setCookieModalOpen] = useState(false);

  const [bgUrl, setBgUrl] = useState<string>(BG.frontpage2);

  useEffect(() => {
    let alive = true;

    // Fallback-Liste: wenn du später ein Landscape-Bild ergänzt, einfach vorne eintragen
    const tryList = [BG.frontpage2, "/images/frontpage_LiftimeCicrcle_safe.webp", "/images/frontpage_LiftimeCicrcle_safe.png"];
    let idx = 0;

    const probe = () => {
      const src = tryList[idx];
      const img = new Image();
      img.onload = () => {
        if (!alive) return;
        setBgUrl(src);
      };
      img.onerror = () => {
        if (!alive) return;
        idx += 1;
        if (idx < tryList.length) probe();
      };
      img.src = src;
    };

    probe();

    return () => {
      alive = false;
    };
  }, []);

  const onLogin = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim();
    if (trimmed) sessionStorage.setItem("ltc_prefill_email", trimmed);
    window.location.hash = "#/auth";
  };

  const trustText =
    "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

  return (
    <div
      className="ltc-app ltc-app--hero"
      style={{
        ["--ltc-bg" as any]: `url("${bgUrl}")`,
        ["--ltc-bg-op" as any]: "1",

        // Ô£à Proportionen/Look wie Beispiel: Hero wirkt wie Banner (cover), Fokus oben/rechts
        ["--ltc-bg-size" as any]: "cover",
        ["--ltc-bg-pos" as any]: "68% 12%",
      }}
    >
      <Topbar
        right={
          <div className="ltc-nav ltc-nav--tight">
            <button type="button" className="ltc-nav__btn" onClick={() => (window.location.hash = "#/")}>
              Home
            </button>
            <button type="button" className="ltc-nav__btn" onClick={() => scrollToId("services")}>
              Services
            </button>
            <button type="button" className="ltc-nav__btn" onClick={() => scrollToId("about")}>
              About
            </button>
            <a href="#/blog" className="ltc-nav__a">
              Blog
            </a>
            <a href="#/auth" className="ltc-pill">
              Login
            </a>
          </div>
        }
      />

      {/* HERO (wie Beispiel): links Copy + Login, rechts Phone/QR Mock */}
      <div className="ltc-container">
        <section className="ltc-hero">
          <div className="ltc-hero__grid">
            <div className="ltc-hero__copy">
              <div className="ltc-hero__panel">
                <h1 className="ltc-hero__h1">
                  Digitales
                  <br />
                  Fahrzeug-Serviceheft
                </h1>
                <div className="ltc-hero__sub">Dokumentation, Vertrauen &amp; Zukunft</div>

                <form className="ltc-hero__form" onSubmit={onLogin}>
                  <div className="ltc-hero__formRow">
                    <input
                      className="ltc-input ltc-input--hero"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Email address"
                      autoComplete="email"
                      aria-label="Email address"
                    />
                    <button type="submit" className="ltc-btn ltc-btn--primary ltc-btn--hero">
                      Log in
                    </button>
                  </div>

                  <div className="ltc-hero__ctaRow">
                    <button type="button" className="ltc-btn ltc-btn--ghost" onClick={() => scrollToId("about")}>
                      Mehr Erfahren
                    </button>
                    <button type="button" className="ltc-btn ltc-btn--soft" onClick={() => scrollToId("services")}>
                      View Services
                    </button>
                  </div>
                </form>

                <div className="ltc-dividerGold" />

                <div className="ltc-hero__iconRow">
                  <div className="ltc-iconItem">
                    <IconShield className="ltc-ic" />
                    <div>Ereignisse &amp; Nachweise sichern</div>
                  </div>
                  <div className="ltc-iconItem">
                    <IconCheck className="ltc-ic" />
                    <div>Verifiziert und nachvollziehbar</div>
                  </div>
                  <div className="ltc-iconItem">
                    <IconQr className="ltc-ic" />
                    <div>Direkte QR-Checks &amp; Reports</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="ltc-hero__mock" aria-hidden="true">
              <div className="ltc-phone">
                <div className="ltc-phone__top">
                  <div className="ltc-phone__cam" />
                  <div className="ltc-phone__speaker" />
                </div>

                <div className="ltc-phone__screen">
                  <div className="ltc-qrMock" />
                  <div className="ltc-verified">
                    <div className="ltc-verified__label">VERIFIZIERT</div>
                    <div className="ltc-verified__badge">
                      <IconCheck className="ltc-verified__ic" />
                    </div>
                  </div>
                </div>

                <div className="ltc-phone__btn" />
              </div>
            </div>
          </div>
        </section>

        {/* Feature Cards (wie Beispiel: 2 große Karten) */}
        <section className="ltc-featureRow">
          <div className="ltc-featureCard">
            <div className="ltc-featureCard__head">
              <IconShield className="ltc-ic2" />
              <div>
                <div className="ltc-featureCard__t">Fahrzeug-Trust Report</div>
                <div className="ltc-muted">Transparente Historie und verlässliche Berichte</div>
              </div>
            </div>
          </div>

          <div className="ltc-featureCard">
            <div className="ltc-featureCard__head">
              <IconCheck className="ltc-ic2" />
              <div>
                <div className="ltc-featureCard__t">Verifizierte Einträge</div>
                <div className="ltc-muted">Wartung, Reparatur &amp; Unfalldokumentation</div>
              </div>
            </div>
          </div>
        </section>

        {/* Showroom Band (Autos-Look wie Beispiel) */}
        <section className="ltc-showroom">
          <div className="ltc-showroom__card">
            <div className="ltc-showroom__meta">
              <span className="ltc-kicker">Nachweise sichtbar machen</span>
              <span className="ltc-muted">– ohne Datenballast im Public/QR</span>
            </div>

            <div className="ltc-showroom__cars" aria-hidden="true">
              <div className="ltc-carTile" />
              <div className="ltc-carTile ltc-carTile--mid" />
              <div className="ltc-carTile ltc-carTile--right" />
            </div>
          </div>
        </section>

        {/* ServiceHeft Band (wie Beispiel: Headline links + Dokument/Tablet Mock rechts) */}
        <section className="ltc-band">
          <div className="ltc-band__grid">
            <div className="ltc-band__copy">
              <div className="ltc-band__kicker">ServiceHeft 4.0</div>
              <div className="ltc-band__h">Dokumentierte Automobilhistorie mit Zukunft.</div>
              <div className="ltc-band__actions">
                <button type="button" className="ltc-btn ltc-btn--ghost" onClick={() => scrollToId("about")}>
                  Mehr Erfahren
                </button>
              </div>
            </div>

            <div className="ltc-band__mock" aria-hidden="true">
              <div className="ltc-docMock">
                <div className="ltc-docMock__paper" />
                <div className="ltc-docMock__paper ltc-docMock__paper--2" />
                <div className="ltc-docMock__tablet">
                  <div className="ltc-docMock__tabletTop">REPORT</div>
                  <div className="ltc-docMock__tabletBadge">
                    <div className="ltc-docMock__tabletLabel">VERIFIZIERT</div>
                    <IconCheck className="ltc-docMock__tabletIc" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pflicht-Disclaimer (wie Beispiel separat sichtbar) */}
        <section className="ltc-disclaimerBand">
          <div className="ltc-disclaimerBand__card">
            <div className="ltc-disclaimerBand__left">
              <IconShield className="ltc-ic2" />
              <div className="ltc-disclaimerBand__text">{trustText}</div>
            </div>
            <button type="button" className="ltc-btn ltc-btn--soft" onClick={() => scrollToId("footer")}>
              Mehr Erfahren
            </button>
          </div>
        </section>

        {/* Services / About bleiben inhaltlich gleich (nur spacing/Container korrekt) */}
        <div id="services" className="ltc-section">
          <div className="ltc-card ltc-card--wide">
            <div className="ltc-card__title">Services</div>
            <ul className="ltc-list">
              <li>Upload &amp; Dokumentenablage (Quarantäne-by-default, Approve nach Scan CLEAN)</li>
              <li>Historie (Einträge, Timeline, Nachweislogik)</li>
              <li>Trust-Ampel (Dokumentations- &amp; Nachweisqualität)</li>
              <li>Public/QR Mini-Check (datenarm, VIN maskiert)</li>
            </ul>
            <div style={{ marginTop: 10 }}>
              <a className="ltc-link" href="#/faq">
                Zu den FAQs →
              </a>
            </div>
          </div>
        </div>

        <div id="about" className="ltc-section">
          <div className="ltc-card ltc-card--wide">
            <div className="ltc-card__title">About</div>

            <div className="ltc-prose">
              <p>
                LifeTimeCircle ist ein Nachweis- und Dokumentationssystem: Es macht sichtbar, <b>was belegt</b> ist – nicht „wie gut/schlecht“ ein
                Fahrzeug technisch ist.
              </p>

              <details className="ltc-details">
                <summary>Mehr lesen: Zeiten des Autokaufs, fehlendes Vertrauen, Nachweise</summary>
                <p>
                  Vertrauen kippt oft dort, wo Dokumente fehlen: Recherche (viel Text, wenig Proof), Besichtigung (Aussagen vs. Belege), Verhandlung
                  (Risikoaufschlag), Übergabe (fehlende Unterlagen), Wiederverkauf (ohne Historie schwer vermittelbar).
                </p>
                <ul>
                  <li>
                    <b>Nachweise erhöhen Vergleichbarkeit:</b> gleiche Fragen, gleiche Belege, bessere Entscheidungen.
                  </li>
                  <li>
                    <b>Proof reduziert Risiko:</b> weniger „Gefühl“, mehr belastbare Historie.
                  </li>
                  <li>
                    <b>Wiederverkauf:</b> saubere Dokumentation kann Vertrauen erhöhen und sich positiv auf den Wiederverkaufswert auswirken.
                  </li>
                </ul>
              </details>
            </div>

            <div className="ltc-quote ltc-quote--gold">
              <div className="ltc-quote__t">Zitat</div>
              <div className="ltc-quote__q">„{trustText}“</div>
            </div>

            <div className="ltc-actions">
              <a className="ltc-btn ltc-btn--soft" href="#/blog">
                Blog ansehen
              </a>
              <button type="button" className="ltc-btn ltc-btn--ghost" onClick={() => setCookieModalOpen(true)}>
                Cookie-Einstellungen
              </button>
            </div>

            {import.meta.env.DEV && (
              <div className="ltc-meta" style={{ marginTop: 12 }}>
                Debug: <a href="#/debug/public-site">#/debug/public-site</a>
              </div>
            )}
          </div>
        </div>
      </div>

      <Footer />

      <CookieBanner onOpenSettings={() => setCookieModalOpen(true)} />

      {cookieModalOpen && (
        <Modal title="Cookie-Einstellungen" onClose={() => setCookieModalOpen(false)}>
          <CookieSettingsCard onSaved={() => setCookieModalOpen(false)} />
        </Modal>
      )}
    </div>
  );
}
/** ---------------------------
 * Static Pages
 * --------------------------- */
function FaqPage() {
  return (
    <StaticShell title="FAQ" bg={getBgForRoute({ kind: "faq" })}>
      <h2>Was ist das ServiceHeft 4.0?</h2>
      <p>
        Ein digitales Nachweis- und Dokumentationssystem: Uploads, Historie und Belege werden strukturiert abgelegt, damit Aussagen prüfbar werden.
      </p>

      <h2>Warum ist das beim Autokauf relevant?</h2>
      <p>
        Vertrauen scheitert oft an fehlenden Unterlagen. Saubere Dokumentation reduziert Unsicherheit und kann beim Wiederverkauf helfen, weil Käufer
        weniger Risiko einpreisen.
      </p>

      <h2>Was zeigt Public/QR?</h2>
      <p>Datenarm (z. B. VIN maskiert), aber geeignet für schnelle Checks &amp; Reports.</p>

      <h2>Wo ändere ich Cookies?</h2>
      <p>
        Unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
    </StaticShell>
  );
}

function CookiesPage() {
  return (
    <StaticShell title="Cookie-Einstellungen" bg={getBgForRoute({ kind: "cookies" })}>
      <CookieSettingsCard />
      <h2>Was wird gespeichert?</h2>
      <p>Technisch notwendige Zustände (z. B. Flow-/Session-Status) und deine Cookie-Auswahl. Marketing/Tracking ist deaktiviert.</p>
    </StaticShell>
  );
}

function JobsPage() {
  return (
    <StaticShell title="Jobs" bg={getBgForRoute({ kind: "jobs" })}>
      <p>Wir suchen Menschen, die Security-First, Datenhygiene und saubere Produktlogik ernst nehmen.</p>
      <h2>Profile</h2>
      <ul>
        <li>Frontend (React/TypeScript, Komponenten, Accessibility)</li>
        <li>Backend (FastAPI, RBAC/Object-Checks, Tests)</li>
        <li>Security/Compliance (PII-Policy, Redaction, Audit-Trails)</li>
      </ul>
      <h2>Bewerbung</h2>
      <p>
        Neutraler Dev-Kontakt: <code>jobs@lifetimecircle.example</code>
      </p>
    </StaticShell>
  );
}

function ImpressumPage() {
  return (
    <StaticShell title="Impressum" bg={getBgForRoute({ kind: "impressum" })}>
      <p>Betreiberangaben sind je Deployment zu konfigurieren. Keine realen Namen/Adressen in Quelltext/Mockups.</p>
      <h2>Kontakt</h2>
      <p>
        Neutral: <code>support@lifetimecircle.example</code>
      </p>
    </StaticShell>
  );
}

function DatenschutzPage() {
  return (
    <StaticShell title="Datenschutz" bg={getBgForRoute({ kind: "datenschutz" })}>
      <p>
        Public/QR ist datenarm (z. B. VIN maskiert). Uploads sind Quarantäne-by-default und werden erst nach Scan freigegeben. Keine PII in
        Mockups/Exports/Logs.
      </p>
      <h2>Consent</h2>
      <p>
        Consent verwaltet die Zustimmung zu Bedingungen/Datenschutz. Seite: <a href="#/consent">#/consent</a>.
      </p>
      <h2>Cookies</h2>
      <p>
        Notwendig ist immer aktiv. Optionales Analytics steuerst du unter <a href="#/cookies">Cookie-Einstellungen</a>.
      </p>
    </StaticShell>
  );
}

/** ---------------------------
 * App Root
 * --------------------------- */
export default function App() {
  const pathQrMatch =
    window.location.pathname.match(/^\/qr\/([^/?#]+)$/) ?? window.location.pathname.match(/^\/public\/qr\/([^/?#]+)$/);

  if (pathQrMatch) {
    const vehicleId = decodeURIComponent(pathQrMatch[1]);
    return (
      <>
        <style>{css}</style>
        <div className="ltc-app ltc-app--plain" style={bgStyle(getBgForRoute({ kind: "publicQr", vehicleId }))}>
          <div className="ltc-container ltc-page">
            <div style={{ marginBottom: 12 }}>
              <a className="ltc-link" href="#/">
                ← Zur Frontpage
              </a>
            </div>
            <PublicQrPage vehicleId={vehicleId} />
          </div>
        </div>
      </>
    );
  }

  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  useEffect(() => {
    const raw = (window.location.hash || "").replace(/^#\/?/, "");
    if (raw.startsWith("public/site")) window.location.replace("#/");
  }, [route.kind]);

  const pageTitle = useMemo(() => {
    switch (route.kind) {
      case "home":
        return "LifeTimeCircle – ServiceHeft 4.0";
      case "debugPublicSite":
        return "Debug: Public Site (API)";
      case "faq":
        return "FAQ";
      case "cookies":
        return "Cookie-Einstellungen";
      case "jobs":
        return "Jobs";
      case "impressum":
        return "Impressum";
      case "datenschutz":
        return "Datenschutz";
      case "blogList":
        return "Blog";
      case "blogPost":
        return `Blog: ${route.slug}`;
      case "newsList":
        return "News";
      case "newsPost":
        return `News: ${route.slug}`;
      case "publicQr":
        return `Public QR: ${route.vehicleId}`;
      case "auth":
        return "Auth";
      case "consent":
        return "Consent";
      case "vehicles":
        return "Vehicles";
      case "vehicleDetail":
        return `Vehicle: ${route.vehicleId}`;
      case "documents":
        return "Documents";
      case "onboarding":
        return "Onboarding";
    }
  }, [route]);

  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);

  const nonHomeBg = getBgForRoute(route);

  return (
    <>
      <style>{css}</style>

      {route.kind === "home" && <FrontPage />}

      {route.kind === "faq" && <FaqPage />}
      {route.kind === "cookies" && <CookiesPage />}
      {route.kind === "jobs" && <JobsPage />}
      {route.kind === "impressum" && <ImpressumPage />}
      {route.kind === "datenschutz" && <DatenschutzPage />}

      {route.kind !== "home" &&
        route.kind !== "faq" &&
        route.kind !== "cookies" &&
        route.kind !== "jobs" &&
        route.kind !== "impressum" &&
        route.kind !== "datenschutz" && (
          <div className="ltc-app ltc-app--plain" style={bgStyle(nonHomeBg)}>
            <div className="ltc-container ltc-page">
              <h1 className="ltc-h1">{pageTitle}</h1>

              <div className="ltc-card">
                <div className="ltc-muted">
                  Scaffold/Debug Container. Produktseiten liegen in <code>packages/web/src/pages/*</code>.
                </div>

                <div style={{ marginTop: 12 }}>
                  <a className="ltc-link" href="#/">
                    ← Zur Frontpage
                  </a>
                  {import.meta.env.DEV && (
                    <>
                      {" "}
                      ·{" "}
                      <a className="ltc-link" href="#/debug/public-site">
                        Debug Public Site
                      </a>
                    </>
                  )}
                </div>
              </div>

              {route.kind === "debugPublicSite" && <ApiBox path="/public/site" title="API: /public/site" />}

              {route.kind === "blogList" && <ItemsList title="Blog (Public)" path="/blog" kind="blog" />}
              {route.kind === "newsList" && <ItemsList title="News (Public)" path="/news" kind="news" />}

              {route.kind === "blogPost" && (
                <PostView
                  title={`Blog Post: ${route.slug}`}
                  path={`/blog/${encodeURIComponent(route.slug)}`}
                  backHref="#/blog"
                  backLabel="zur Blog-Liste"
                />
              )}

              {route.kind === "newsPost" && (
                <PostView
                  title={`News Post: ${route.slug}`}
                  path={`/news/${encodeURIComponent(route.slug)}`}
                  backHref="#/news"
                  backLabel="zur News-Liste"
                />
              )}

              {route.kind === "publicQr" && (
                <div style={{ marginTop: 12 }}>
                  <PublicQrPage vehicleId={decodeURIComponent(route.vehicleId)} />
                </div>
              )}

              {route.kind === "auth" && <AuthPage />}
              {route.kind === "consent" && <ConsentPage />}
              {route.kind === "vehicles" && <VehiclesPage />}
              {route.kind === "vehicleDetail" && <VehicleDetailPage />}
              {route.kind === "documents" && <DocumentsPage />}
              {route.kind === "onboarding" && <OnboardingWizardPage />}

              <Footer />
            </div>
          </div>
        )}
    </>
  );
}
/** ---------------------------
 * CSS – Frame + Container identisch breit (Proportionen-Fix) + neue Frontpage Styles
 * --------------------------- */
const css = String.raw`
:root{
  --ltc-bg0:#070a0f;
  --ltc-fg:rgba(255,255,255,.92);
  --ltc-muted:rgba(255,255,255,.72);
  --ltc-line:rgba(255,255,255,.12);
  --ltc-glass:rgba(255,255,255,.05);
  --ltc-gold: rgba(201,168,106, 0.95);
  --ltc-gold2: rgba(201,168,106, 0.35);
  --ltc-shadow:0 18px 60px rgba(0,0,0,.55);

  /* Frame: Background-Fenster */
  --ltc-frame-max: 1500px;
  --ltc-frame-gutter: 24px;
}

*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  background:var(--ltc-bg0);
  color:var(--ltc-fg);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
}
a{color:inherit}
code{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace}

/* Ô£à Fix: Container hat EXAKT dieselbe Breitenlogik wie der Background-Frame */
.ltc-container{
  width: min(var(--ltc-frame-max, 1500px), calc(100vw - (2 * var(--ltc-frame-gutter, 24px))));
  margin: 0 auto;
  padding: 0 18px;
}

.ltc-app{ min-height:100vh; color:var(--ltc-fg); }

/* -----------------------------------------
   Background Engine: Bild NUR im Frame
------------------------------------------ */
.ltc-app--plain,
.ltc-app--hero{
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background: var(--ltc-bg0);
}

/* Bild-Frame */
.ltc-app--plain::before,
.ltc-app--hero::before{
  content:"";
  position: fixed;
  top: 0;
  bottom: 0;
  left: 50%;
  width: min(var(--ltc-frame-max, 1500px), calc(100vw - (2 * var(--ltc-frame-gutter, 24px))));
  transform: translateX(-50%);
  z-index: -2;
  pointer-events: none;

  background-image: var(--ltc-bg);
  background-repeat: no-repeat;
  background-size: var(--ltc-bg-size, cover);
  background-position: var(--ltc-bg-pos, center);

  opacity: var(--ltc-bg-op, 0);
  filter: saturate(1.05) contrast(1.03);
}

/* Overlay über ALLES */
.ltc-app--plain::after{
  content:"";
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(1100px 700px at 12% 10%, rgba(201,168,106,.14), transparent 60%),
    radial-gradient(900px 600px at 88% 18%, rgba(255,255,255,.05), transparent 55%),
    linear-gradient(to bottom, rgba(0,0,0,.44), rgba(0,0,0,.74));
}

/* HERO Overlay (mehr “Banner”-Look) */
.ltc-app--hero::after{
  content:"";
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(1200px 520px at 20% 18%, rgba(201,168,106,.18), transparent 60%),
    radial-gradient(980px 620px at 85% 26%, rgba(201,168,106,.10), transparent 65%),
    linear-gradient(180deg, rgba(0,0,0,.62) 0%, rgba(0,0,0,.72) 55%, rgba(0,0,0,.84) 100%);
}

/* Topbar */
.ltc-topbar{
  position: sticky;
  top: 0;
  z-index: 70;
  padding: 12px 0;
  background: linear-gradient(180deg, rgba(0,0,0,.72) 0%, rgba(0,0,0,.35) 70%, rgba(0,0,0,0) 100%);
  backdrop-filter: blur(10px);
}
.ltc-topbar__line{
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(201,168,106,.50), transparent);
  opacity: .9;
}
.ltc-topbar__inner{ display:flex; align-items:center; justify-content:space-between; gap:14px; }
.ltc-topbar__right{ display:flex; justify-content:flex-end; }

.ltc-brand{
  display:flex; align-items:center; gap:12px;
  text-decoration:none;
  color: rgba(255,255,255,.92);
}
.ltc-brand__mark{
  width:14px;height:14px;border-radius:999px;
  border:1px solid rgba(201,168,106,.40);
  box-shadow: 0 0 0 3px rgba(201,168,106,.10);
}
.ltc-brand__text{ display:flex; flex-direction:column; line-height:1.05; }
.ltc-brand__name{ font-size:13px; letter-spacing:.18em; font-weight:950; }
.ltc-brand__sub{ font-size:10px; letter-spacing:.22em; opacity:.72; margin-top:2px; }

.ltc-nav{
  display:flex; align-items:center; justify-content:flex-end;
  gap:10px; flex-wrap:wrap;
}
.ltc-nav--tight{ gap: 10px; }

.ltc-nav__a,
.ltc-nav__btn{
  appearance:none;
  background:transparent;
  border:1px solid transparent;
  color: rgba(255,255,255,.82);
  font-size:12px;
  letter-spacing:.10em;
  text-transform:uppercase;
  padding:8px 10px;
  border-radius:999px;
  cursor:pointer;
  text-decoration:none;
  font-weight:850;
  line-height:1;
}
.ltc-nav__a:hover,
.ltc-nav__btn:hover{
  background: rgba(255,255,255,.05);
  border-color: rgba(255,255,255,.12);
}

.ltc-pill{
  display:inline-flex; align-items:center; justify-content:center;
  padding:9px 12px;
  border-radius:999px;
  border:1px solid rgba(201,168,106,.34);
  background: rgba(0,0,0,.28);
  color: rgba(255,255,255,.92);
  text-decoration:none;
  font-size:12px;
  letter-spacing:.10em;
  text-transform:uppercase;
  font-weight:900;
}
.ltc-pill:hover{
  border-color: rgba(201,168,106,.52);
  background: rgba(255,255,255,.06);
}
@media (max-width: 720px){
  .ltc-topbar{ padding: 10px 0; }
  .ltc-nav__a,.ltc-nav__btn,.ltc-pill{ padding: 7px 9px; font-size: 11px; }
}

/* Inputs + Buttons */
.ltc-input{
  width:340px;max-width:100%;
  padding:12px 14px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.16);
  background:rgba(0,0,0,.34);
  color:rgba(255,255,255,.92);
  outline:none;
  box-shadow:0 16px 44px rgba(0,0,0,.34);
}
.ltc-input--hero{ width: 420px; }
.ltc-input:focus{
  border-color:rgba(201,168,106,.35);
  box-shadow:0 18px 46px rgba(0,0,0,.36), 0 0 0 1px rgba(201,168,106,.20) inset
}

.ltc-btn{
  padding:12px 16px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.16);
  cursor:pointer;
  color:rgba(255,255,255,.92);
  font-weight:900;
  background:rgba(255,255,255,.06);
  transition: transform .12s ease, background .12s ease, border-color .12s ease;
  text-decoration:none;
  display:inline-flex;align-items:center;justify-content:center;
}
.ltc-btn:hover{
  transform:translateY(-1px);
  border-color:rgba(201,168,106,.30);
  background:rgba(255,255,255,.08)
}
.ltc-btn:active{ transform:translateY(0px) }
.ltc-btn--primary{
  border-color:rgba(201,168,106,.42);
  background: linear-gradient(180deg, rgba(201,168,106,.16), rgba(0,0,0,.26));
  box-shadow: 0 14px 34px rgba(0,0,0,.35), 0 0 24px rgba(201,168,106,.14);
}
.ltc-btn--soft{ background:rgba(0,0,0,.30); border-color:rgba(255,255,255,.14); font-weight:900 }
.ltc-btn--ghost{ background:transparent; border-color:rgba(201,168,106,.22); font-weight:900 }
.ltc-btn--hero{ min-width:120px }

.ltc-dividerGold{
  height:1px;
  margin:18px 0 14px 0;
  background: linear-gradient(90deg, transparent, rgba(201,168,106,.55), transparent);
  opacity:.9;
}

/* Icons */
.ltc-ic{ width:18px;height:18px;color:rgba(201,168,106,.85) }
.ltc-ic2{ width:22px;height:22px;color:rgba(201,168,106,.90) }

.ltc-iconItem{
  display:flex;
  align-items:center;
  gap:10px;
  min-width:0;
}
.ltc-iconItem > div{ min-width:0; }

/* --------------------------
   FRONT PAGE (NEU)
-------------------------- */
.ltc-hero{
  padding: 22px 0 0 0;
}
.ltc-hero__grid{
  display:grid;
  grid-template-columns: 1.05fr .95fr;
  gap: 18px;
  align-items: stretch;
}
@media (max-width: 980px){
  .ltc-hero__grid{ grid-template-columns: 1fr; }
}

.ltc-hero__copy{ min-width:0; }
.ltc-hero__panel{
  border-radius: 20px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(0,0,0,.30);
  backdrop-filter: blur(12px);
  box-shadow: var(--ltc-shadow);
  padding: 22px;
  position: relative;
  overflow:hidden;
}
.ltc-hero__panel:before{
  content:"";
  position:absolute; inset:0;
  background: radial-gradient(740px 260px at 18% 0%, rgba(201,168,106,.12), transparent 60%);
  pointer-events:none;
}

.ltc-hero__h1{
  margin:0;
  font-size: clamp(38px, 4vw, 56px);
  letter-spacing:-0.9px;
  line-height:1.02;
  font-weight:950;
  text-shadow: 0 18px 46px rgba(0,0,0,.62);
  position:relative;
}
.ltc-hero__sub{
  margin-top:10px;
  font-size:18px;
  opacity:.86;
  line-height:1.55;
  text-shadow: 0 14px 36px rgba(0,0,0,.50);
  position:relative;
}

.ltc-hero__form{ margin-top: 16px; position:relative; }
.ltc-hero__formRow{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
}
.ltc-hero__ctaRow{
  margin-top: 12px;
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}

/* Ô£à 3 Punkte wie Beispiel: Desktop nebeneinander */
.ltc-hero__iconRow{
  display:grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px 18px;
  font-size:13px;
  opacity:.92;
  align-items:center;
  position:relative;
}
@media (max-width: 860px){
  .ltc-hero__iconRow{ grid-template-columns: 1fr; }
}

/* Right side phone mock */
.ltc-hero__mock{
  display:flex;
  align-items:center;
  justify-content:center;
  min-height: 380px;
}
@media (max-width: 980px){
  .ltc-hero__mock{ min-height: 320px; }
}

.ltc-phone{
  width: min(320px, 100%);
  aspect-ratio: 9 / 16;
  border-radius: 28px;
  border: 1px solid rgba(201,168,106,.22);
  background: rgba(0,0,0,.45);
  box-shadow: 0 22px 64px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.06) inset;
  position: relative;
  overflow: hidden;
}
.ltc-phone:before{
  content:"";
  position:absolute; inset:0;
  background:
    radial-gradient(520px 240px at 70% 20%, rgba(201,168,106,.18), transparent 60%),
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(0,0,0,.10));
  pointer-events:none;
}
.ltc-phone__top{
  position:absolute; top:10px; left:0; right:0;
  display:flex; align-items:center; justify-content:center;
  gap:10px;
  z-index:2;
}
.ltc-phone__cam{
  width:10px;height:10px;border-radius:999px;
  background: rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.10);
}
.ltc-phone__speaker{
  width:56px;height:8px;border-radius:999px;
  background: rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.08);
}
.ltc-phone__screen{
  position:absolute; inset: 34px 14px 34px 14px;
  border-radius: 18px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(0,0,0,.35);
  overflow:hidden;
  z-index:1;
  display:flex;
  align-items:center;
  justify-content:center;
}
.ltc-phone__btn{
  position:absolute; bottom:10px; left:50%;
  transform: translateX(-50%);
  width: 72px;
  height: 8px;
  border-radius: 999px;
  background: rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.10);
  z-index:2;
}

/* QR mock */
.ltc-qrMock{
  width: 70%;
  aspect-ratio: 1 / 1;
  border-radius: 14px;
  background:
    linear-gradient(90deg, rgba(255,255,255,.10) 1px, transparent 1px),
    linear-gradient(180deg, rgba(255,255,255,.10) 1px, transparent 1px),
    radial-gradient(240px 240px at 40% 40%, rgba(201,168,106,.18), transparent 60%),
    rgba(0,0,0,.24);
  background-size: 10px 10px, 10px 10px, auto, auto;
  border:1px solid rgba(255,255,255,.12);
  box-shadow: 0 18px 44px rgba(0,0,0,.35);
}

/* Verified badge */
.ltc-verified{
  position:absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding: 10px 12px;
  border-radius: 14px;
  border:1px solid rgba(201,168,106,.24);
  background: rgba(0,0,0,.38);
  backdrop-filter: blur(10px);
}
.ltc-verified__label{
  font-weight: 950;
  letter-spacing: .12em;
  font-size: 12px;
  color: rgba(201,168,106,.95);
}
.ltc-verified__badge{
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border:1px solid rgba(201,168,106,.34);
  background: rgba(201,168,106,.12);
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow: 0 0 20px rgba(201,168,106,.16);
}
.ltc-verified__ic{ width: 18px; height: 18px; color: rgba(255,255,255,.92); }

/* Feature cards row */
.ltc-featureRow{
  margin-top: 16px;
  display:grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
@media (max-width: 980px){
  .ltc-featureRow{ grid-template-columns: 1fr; }
}
.ltc-featureCard{
  border-radius:18px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(255,255,255,.04);
  backdrop-filter: blur(10px);
  box-shadow: 0 18px 60px rgba(0,0,0,.22);
  padding:18px;
  position:relative;
  overflow:hidden;
}
.ltc-featureCard:before{
  content:"";
  position:absolute; inset:0;
  background: radial-gradient(520px 180px at 20% 10%, rgba(201,168,106,.12), transparent 60%);
  pointer-events:none;
}
.ltc-featureCard__head{ display:flex; gap:12px; align-items:flex-start; position:relative; }
.ltc-featureCard__t{ font-weight:950; font-size:18px; margin-bottom:2px }

/* Showroom band */
.ltc-showroom{ margin-top: 14px; }
.ltc-showroom__card{
  border-radius: 20px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(0,0,0,.26);
  backdrop-filter: blur(12px);
  box-shadow: var(--ltc-shadow);
  padding: 18px;
  position:relative;
  overflow:hidden;
}
.ltc-showroom__card:before{
  content:"";
  position:absolute; inset:0;
  background:
    radial-gradient(900px 320px at 30% 0%, rgba(201,168,106,.12), transparent 60%),
    radial-gradient(700px 260px at 80% 120%, rgba(255,255,255,.05), transparent 55%);
  pointer-events:none;
}
.ltc-showroom__meta{ position:relative; display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }
.ltc-kicker{
  font-weight: 950;
  letter-spacing: .10em;
  text-transform: uppercase;
  font-size: 12px;
  color: rgba(201,168,106,.92);
}

.ltc-showroom__cars{
  position:relative;
  margin-top: 14px;
  display:grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  align-items:end;
  min-height: 120px;
}
@media (max-width: 860px){
  .ltc-showroom__cars{ grid-template-columns: 1fr; min-height:auto; }
}
.ltc-carTile{
  height: 120px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,.10);
  background:
    radial-gradient(220px 120px at 30% 40%, rgba(255,255,255,.10), transparent 60%),
    radial-gradient(260px 140px at 70% 60%, rgba(201,168,106,.14), transparent 65%),
    rgba(255,255,255,.03);
  box-shadow: 0 18px 54px rgba(0,0,0,.30);
}
.ltc-carTile--mid{ height: 132px; }
.ltc-carTile--right{ height: 124px; }

/* Service band */
.ltc-band{ margin-top: 14px; }
.ltc-band__grid{
  border-radius: 20px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(255,255,255,.04);
  backdrop-filter: blur(12px);
  box-shadow: var(--ltc-shadow);
  padding: 18px;
  display:grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 18px;
  align-items:center;
  position:relative;
  overflow:hidden;
}
.ltc-band__grid:before{
  content:"";
  position:absolute; inset:0;
  background: radial-gradient(820px 280px at 18% 0%, rgba(201,168,106,.10), transparent 60%);
  pointer-events:none;
}
@media (max-width: 980px){
  .ltc-band__grid{ grid-template-columns: 1fr; }
}
.ltc-band__copy{ position:relative; }
.ltc-band__kicker{
  font-weight: 950;
  letter-spacing: -.8px;
  font-size: 44px;
  line-height:1.0;
}
.ltc-band__h{
  margin-top: 6px;
  font-size: 16px;
  opacity: .86;
  line-height: 1.55;
}
.ltc-band__actions{ margin-top: 12px; display:flex; gap:10px; flex-wrap:wrap; position:relative; }

.ltc-docMock{
  position:relative;
  min-height: 220px;
  display:flex;
  align-items:flex-end;
  justify-content:flex-end;
}
.ltc-docMock__paper{
  position:absolute;
  left: 10px;
  bottom: 14px;
  width: 58%;
  height: 70%;
  border-radius: 14px;
  border:1px solid rgba(255,255,255,.10);
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(0,0,0,.22)),
    rgba(255,255,255,.03);
  box-shadow: 0 18px 54px rgba(0,0,0,.32);
}
.ltc-docMock__paper--2{
  left: 26px;
  bottom: 22px;
  width: 54%;
  height: 64%;
  opacity: .88;
}
.ltc-docMock__tablet{
  position:relative;
  width: 52%;
  height: 86%;
  min-height: 210px;
  border-radius: 18px;
  border:1px solid rgba(201,168,106,.22);
  background: rgba(0,0,0,.34);
  box-shadow: 0 22px 64px rgba(0,0,0,.45);
  overflow:hidden;
}
.ltc-docMock__tablet:before{
  content:"";
  position:absolute; inset:0;
  background:
    radial-gradient(420px 220px at 70% 20%, rgba(201,168,106,.18), transparent 60%),
    linear-gradient(180deg, rgba(255,255,255,.05), rgba(0,0,0,.18));
  pointer-events:none;
}
.ltc-docMock__tabletTop{
  position:absolute; top: 10px; left: 12px;
  font-weight: 950;
  letter-spacing: .14em;
  font-size: 12px;
  opacity: .86;
}
.ltc-docMock__tabletBadge{
  position:absolute; right: 12px; bottom: 12px;
  border-radius: 14px;
  border:1px solid rgba(201,168,106,.22);
  background: rgba(0,0,0,.38);
  padding: 10px 10px;
  display:flex;
  align-items:center;
  gap:10px;
}
.ltc-docMock__tabletLabel{
  font-weight: 950;
  letter-spacing: .10em;
  font-size: 11px;
  color: rgba(201,168,106,.95);
}
.ltc-docMock__tabletIc{ width: 18px; height: 18px; color: rgba(255,255,255,.92); }

/* Disclaimer band */
.ltc-disclaimerBand{ margin-top: 14px; margin-bottom: 8px; }
.ltc-disclaimerBand__card{
  border-radius: 18px;
  border:1px solid rgba(201,168,106,.18);
  background: rgba(0,0,0,.30);
  backdrop-filter: blur(10px);
  box-shadow: 0 18px 60px rgba(0,0,0,.30);
  padding: 14px 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.ltc-disclaimerBand__left{ display:flex; align-items:center; gap: 10px; min-width: 0; }
.ltc-disclaimerBand__text{ opacity:.88; line-height: 1.5; max-width: 920px; }

/* Sections */
.ltc-section{ padding: 12px 0 0 0; }

/* Cards / Prose (bestehende Klassen weiter genutzt) */
.ltc-card{
  border:1px solid rgba(255,255,255,.10);
  border-radius:18px;
  background:rgba(255,255,255,.04);
  backdrop-filter: blur(10px);
  padding:18px;
  box-shadow: 0 14px 34px rgba(0,0,0,.22);
}
.ltc-card--wide{ position:relative; overflow:hidden }
.ltc-card--wide:before{
  content:"";
  position:absolute; inset:0;
  background: radial-gradient(740px 240px at 18% 0%, rgba(201,168,106,.10), transparent 60%);
  pointer-events:none;
}
.ltc-card__title{ font-weight:950;font-size:18px;margin-bottom:10px; position:relative }
.ltc-muted{ opacity:.82;line-height:1.55;color:var(--ltc-muted) }
.ltc-strong{ font-weight:900 }
.ltc-meta{ font-size:12px;opacity:.78;margin:10px 0; position:relative }
.ltc-pre{ white-space:pre-wrap;margin:0;font-size:13px;line-height:1.35 }
.ltc-list{ margin:0;padding-left:18px;line-height:1.7; position:relative }
.ltc-link{ text-decoration:none;color:rgba(255,255,255,.90) }
.ltc-link:hover{ text-decoration:underline }

.ltc-quote{
  margin-top:14px;
  padding:14px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,.10);
  background: rgba(0,0,0,.26);
  position:relative;
}
.ltc-quote--gold{
  border-color: rgba(201,168,106,.22);
  box-shadow: 0 0 0 1px rgba(201,168,106,.10) inset;
}
.ltc-quote__t{ font-weight:900;margin-bottom:6px }
.ltc-quote__q{ font-style:italic;opacity:.92;line-height:1.6 }

.ltc-details{ margin-top:10px; position:relative }
.ltc-details summary{ cursor:pointer;font-weight:900 }
.ltc-details p{ margin-top:10px }
.ltc-prose{ line-height:1.75;opacity:.92; position:relative }
.ltc-prose p{ margin:10px 0 }
.ltc-prose ul{ margin:8px 0 0 18px }

/* Footer */
.ltc-footer{
  margin-top:26px;
  border-top:1px solid rgba(255,255,255,.10);
  background: rgba(0,0,0,.62);
  backdrop-filter: blur(10px);
}
.ltc-footer__grid{
  padding:22px 0;
  display:grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap:18px;
}
.ltc-footer__title{ font-weight:950;margin-bottom:10px }
.ltc-footer__links{ display:grid;gap:8px }
.ltc-footer__links a{ color:rgba(255,255,255,.80);text-decoration:none }
.ltc-footer__links a:hover{ text-decoration:underline }
.ltc-footer__bottom{ padding:0 0 18px 0;font-size:12px;opacity:.72 }

/* Cookie */
.ltc-cookie{
  position:fixed;
  left:14px; right:14px; bottom:14px;
  z-index:80;
  max-width:1100px;
  margin:0 auto;
  border-radius:16px;
  border:1px solid rgba(201,168,106,.18);
  background: rgba(0,0,0,.82);
  backdrop-filter: blur(10px);
  box-shadow: var(--ltc-shadow);
  padding:14px;
}
.ltc-cookie__title{ font-weight:950;margin-bottom:6px }
.ltc-cookie__text{ font-size:13px;opacity:.86;line-height:1.45 }
.ltc-cookie__text a{ color:rgba(255,255,255,.92) }
.ltc-cookie__actions{ margin-top:12px;display:flex;gap:10px;flex-wrap:wrap }

.ltc-row{ display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0 }
.ltc-check{ width:18px;height:18px;accent-color:#fff }
.ltc-divider{ height:1px;background:rgba(255,255,255,.10);margin:10px 0 }
.ltc-actions{ margin-top:14px;display:flex;gap:10px;flex-wrap:wrap }

.ltc-modal{
  position:fixed; inset:0;
  background:rgba(0,0,0,.62);
  z-index:90;
  display:flex; align-items:center; justify-content:center;
  padding:14px;
}
.ltc-modal__card{
  width:min(860px, 100%);
  max-height:85vh;
  overflow:auto;
  border-radius:16px;
  border:1px solid rgba(201,168,106,.18);
  background:rgba(0,0,0,.88);
  backdrop-filter: blur(10px);
  box-shadow: var(--ltc-shadow);
}
.ltc-modal__head{ display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px }
.ltc-modal__body{ padding:12px }

/* Plain pages */
.ltc-page{ padding:28px 0 0 0 }
.ltc-h1{ margin:0 0 14px 0;font-size:34px;letter-spacing:-.6px }
`;
