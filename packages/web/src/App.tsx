// packages/web/src/App.tsx
import { useEffect, useMemo, useState } from "react";
import { apiGet, asString, isRecord, prettyBody } from "./api";
import { TrustAmpelDisclaimer } from "./components/TrustAmpelDisclaimer";

import { PublicQrPage } from "./pages/PublicQrPage";

import AuthPage from "./pages/AuthPage";
import ConsentPage from "./pages/ConsentPage";
import VehiclesPage from "./pages/VehiclesPage";
import VehicleDetailPage from "./pages/VehicleDetailPage";
import DocumentsPage from "./pages/DocumentsPage";
import OnboardingWizardPage from "./pages/OnboardingWizardPage";

type Route =
  | { kind: "home" }
  | { kind: "publicSite" }
  | { kind: "blogList" }
  | { kind: "blogPost"; slug: string }
  | { kind: "newsList" }
  | { kind: "newsPost"; slug: string }
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

  // existing
  if (parts[0] === "public" && parts[1] === "site") return { kind: "publicSite" };
  if (parts[0] === "blog" && parts.length === 1) return { kind: "blogList" };
  if (parts[0] === "blog" && parts[1]) return { kind: "blogPost", slug: parts[1] };
  if (parts[0] === "news" && parts.length === 1) return { kind: "newsList" };
  if (parts[0] === "news" && parts[1]) return { kind: "newsPost", slug: parts[1] };

  // new scaffolds (hash-based, no router dependency)
  if (parts[0] === "auth") return { kind: "auth" };
  if (parts[0] === "consent") return { kind: "consent" };
  if (parts[0] === "vehicles" && parts.length === 1) return { kind: "vehicles" };
  if (parts[0] === "vehicles" && parts[1]) return { kind: "vehicleDetail", vehicleId: parts[1] };
  if (parts[0] === "documents") return { kind: "documents" };
  if (parts[0] === "onboarding") return { kind: "onboarding" };

  return { kind: "home" };
}

function Nav() {
  const linkStyle: React.CSSProperties = { marginRight: 12, textDecoration: "none" };
  return (
    <nav style={{ marginBottom: 16 }}>
      <a href="#/" style={linkStyle}>
        Home
      </a>
      <a href="#/public/site" style={linkStyle}>
        Public Site
      </a>
      <a href="#/blog" style={linkStyle}>
        Blog
      </a>
      <a href="#/news" style={linkStyle}>
        News
      </a>

      <span style={{ margin: "0 10px", opacity: 0.35 }}>|</span>

      <a href="#/auth" style={linkStyle}>
        Auth
      </a>
      <a href="#/consent" style={linkStyle}>
        Consent
      </a>
      <a href="#/vehicles" style={linkStyle}>
        Vehicles
      </a>
      <a href="#/documents" style={linkStyle}>
        Documents
      </a>
    </nav>
  );
}

function Card(props: { title: string; children: React.ReactNode }) {
  return (
    <section
      style={{
        border: "1px solid rgba(0,0,0,0.12)",
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <h2 style={{ margin: "0 0 12px 0" }}>{props.title}</h2>
      {props.children}
    </section>
  );
}

function ApiBox(props: { path: string; title: string }) {
  const [state, setState] = useState<{ loading: boolean; text: string; status?: number }>({
    loading: true,
    text: "",
  });

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

      setState({
        loading: false,
        text: prettyBody(r.body),
        status: r.status,
      });
    });

    return () => {
      alive = false;
    };
  }, [props.path]);

  return (
    <Card title={props.title}>
      <div style={{ fontSize: 12, opacity: 0.85, marginBottom: 8 }}>
        GET <code>{`/api${props.path.startsWith("/") ? props.path : `/${props.path}`}`}</code>
        {typeof state.status === "number" ? ` → ${state.status}` : ""}
      </div>
      {state.loading ? (
        <div>Lädt…</div>
      ) : (
        <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 13, lineHeight: 1.35 }}>{state.text}</pre>
      )}
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
        setState({
          loading: false,
          status: r.status,
          error: `${r.error}${r.body ? `: ${String(r.body)}` : ""}`,
        });
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
      <div style={{ fontSize: 12, opacity: 0.85, marginBottom: 8 }}>
        GET <code>{`/api${props.path.startsWith("/") ? props.path : `/${props.path}`}`}</code>
        {typeof state.status === "number" ? ` → ${state.status}` : ""}
      </div>

      {state.loading ? (
        <div>Lädt…</div>
      ) : state.error ? (
        <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 13, lineHeight: 1.35 }}>{state.error}</pre>
      ) : state.items ? (
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          {state.items.map((it) => (
            <li key={it.slug} style={{ marginBottom: 6 }}>
              <a href={`#/${props.kind}/${encodeURIComponent(it.slug)}`}>{it.title}</a>{" "}
              <span style={{ fontSize: 12, opacity: 0.7 }}>({it.slug})</span>
            </li>
          ))}
        </ul>
      ) : (
        <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 13, lineHeight: 1.35 }}>{state.raw ?? ""}</pre>
      )}
    </Card>
  );
}

function PostView(props: { title: string; path: string; backHref: string; backLabel: string }) {
  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <a href={props.backHref}>← {props.backLabel}</a>
      </div>
      <ApiBox path={props.path} title={props.title} />
    </>
  );
}

export default function App() {
  // hard route: /qr/:vehicleId (Public QR landing)
  const qrMatch = window.location.pathname.match(/^\/qr\/([^/?#]+)$/);
  if (qrMatch) {
    return <PublicQrPage vehicleId={decodeURIComponent(qrMatch[1])} />;
  }

  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const pageTitle = useMemo(() => {
    switch (route.kind) {
      case "home":
        return "LifeTimeCircle – Service Heft 4.0";
      case "publicSite":
        return "Public Site (API)";
      case "blogList":
        return "Blog";
      case "blogPost":
        return `Blog: ${route.slug}`;
      case "newsList":
        return "News";
      case "newsPost":
        return `News: ${route.slug}`;
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
    }
  }, [route]);

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: 16 }}>
      <header style={{ marginBottom: 16 }}>
        <h1 style={{ margin: "0 0 10px 0" }}>{pageTitle}</h1>
        <Nav />
      </header>

      {route.kind === "home" && (
        <>
          <Card title="Status">
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>
                Web: <code>http://127.0.0.1:5173</code>
              </li>
              <li>
                API: <code>http://127.0.0.1:8000</code>
              </li>
              <li>
                Proxy: <code>/api/*</code> → <code>http://127.0.0.1:8000/*</code>
              </li>
            </ul>
            <TrustAmpelDisclaimer />
          </Card>

          <ApiBox path="/public/site" title="API: /public/site" />
        </>
      )}

      {route.kind === "publicSite" && (
        <>
          <ApiBox path="/public/site" title="API: /public/site" />
          <TrustAmpelDisclaimer />
        </>
      )}

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

      {route.kind === "auth" && <AuthPage />}
      {route.kind === "consent" && <ConsentPage />}
      {route.kind === "vehicles" && <VehiclesPage />}
      {route.kind === "vehicleDetail" && <VehicleDetailPage />}
      {route.kind === "documents" && <DocumentsPage />}
      {route.kind === "onboarding" && <OnboardingWizardPage />}
    </div>
  );
}


