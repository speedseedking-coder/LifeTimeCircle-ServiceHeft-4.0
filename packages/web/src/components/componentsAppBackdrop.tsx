import { type CSSProperties, type ReactNode, useEffect, useMemo, useState } from "react";
import "./AppBackdrop.css";

/**
 * NOTE:
 * Diese App nutzt Hash-Routing (#/auth, #/vehicles/123, ...).
 * Wir leiten daraus eine "pathname"-ähnliche Sicht ab (ohne react-router-dom).
 */
function getHashPathname(): string {
  const raw = (window.location.hash || "").replace(/^#\/?/, "");
  const clean = raw.split("?")[0].split("#")[0];
  if (!clean) return "/";
  return `/${clean}`;
}

function useHashPathname(): string {
  const [pathname, setPathname] = useState<string>(() => getHashPathname());

  useEffect(() => {
    const onHashChange = () => setPathname(getHashPathname());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return pathname;
}

type BgConfig = {
  src: string;
  size?: string;
  position?: string;
  opacity?: number; // 0..1
};

const BG = {
  invoices: "/images/rechnungspruefer.png",
  vehicles: "/images/service2.png",
  serviceheft: "/images/serviceheft.png",
  termsFaq: "/images/terms_faq.png",
  blog: "/images/Blog.png",
  cookies: "/images/cookies.png",
  consent: "/images/daten_zustim.png",
  privacy: "/images/datenschutz.png",
  frontpage: "/images/frontpage_LiftimeCicrcle_2.png",
  galerie: "/images/galerie.png",
  jobs: "/images/jobs.png",
  news: "/images/news.png",
} as const;

function pickBackground(pathname: string): BgConfig | null {
  // Public Landing / Auth: Bild eher rechts ausrichten (passt zur "Right-Gutter" Optik)
  if (pathname === "/" || pathname.startsWith("/public/site")) {
    return { src: BG.frontpage, size: "cover", position: "right center", opacity: 0.30 };
  }
  if (pathname.startsWith("/auth")) {
    return { src: BG.frontpage, size: "cover", position: "right center", opacity: 0.26 };
  }

  // Consent
  if (pathname.startsWith("/consent")) {
    return { src: BG.consent, size: "cover", position: "center", opacity: 0.28 };
  }

  // Public legal pages (Footer)
  if (
    pathname.startsWith("/public/terms") ||
    pathname.startsWith("/public/faq") ||
    pathname.startsWith("/public/impressum")
  ) {
    return { src: BG.termsFaq, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/public/cookies")) {
    return { src: BG.cookies, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/public/privacy") || pathname.startsWith("/public/datenschutz")) {
    return { src: BG.privacy, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/public/jobs")) {
    return { src: BG.jobs, size: "cover", position: "center", opacity: 0.26 };
  }

  // Content
  if (pathname.startsWith("/blog")) {
    return { src: BG.blog, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/news")) {
    return { src: BG.news, size: "cover", position: "center", opacity: 0.26 };
  }

  // Vehicles (specific first)
  if (pathname.includes("/gallery") && pathname.startsWith("/vehicles/")) {
    return { src: BG.galerie, size: "cover", position: "center", opacity: 0.26 };
  }
  if ((pathname.includes("/invoices") || pathname.includes("/archive")) && pathname.startsWith("/vehicles/")) {
    return { src: BG.invoices, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/vehicles/")) {
    return { src: BG.serviceheft, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname === "/vehicles") {
    return { src: BG.vehicles, size: "cover", position: "center", opacity: 0.26 };
  }

  return null;
}

export function AppBackdrop(props: { children: ReactNode }) {
  const pathname = useHashPathname();
  const cfg = useMemo(() => pickBackground(pathname), [pathname]);

  const style = useMemo(() => {
    const base: CSSProperties = {
      ["--ltc-bg-opacity" as any]: "0",
      ["--ltc-bg-size" as any]: "cover",
      ["--ltc-bg-position" as any]: "center",
      ["--ltc-bg-url" as any]: "none",
    };

    if (!cfg) return base;

    return {
      ...base,
      ["--ltc-bg-url" as any]: `url(${cfg.src})`,
      ["--ltc-bg-size" as any]: cfg.size ?? "cover",
      ["--ltc-bg-position" as any]: cfg.position ?? "center",
      ["--ltc-bg-opacity" as any]: String(cfg.opacity ?? 0.26),
    };
  }, [cfg]);

  return (
    <div className="ltc-bg" style={style}>
      <div className="ltc-bg__image" aria-hidden="true" />
      <div className="ltc-bg__overlay" aria-hidden="true" />

      {/* Right-Gutter: Content links, rechts "Luft" -> Background peek */}
      <div className="ltc-shell">{props.children}</div>
    </div>
  );
}
