import React, { ReactNode, useMemo } from "react";
import { useLocation } from "react-router-dom";
import "./AppBackdrop.css";

type BgConfig = {
  src: string;
  /** CSS background-size value, e.g. "cover", "contain", "92% auto" */
  size?: string;
  /** CSS background-position value */
  position?: string;
  /** 0..1 */
  opacity?: number;
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
  // --- Public Landing / Entry
  if (pathname === "/" || pathname.startsWith("/public/site")) {
    return { src: BG.frontpage, size: "92% auto", position: "center", opacity: 0.30 };
  }
  if (pathname.startsWith("/auth")) {
    return { src: BG.frontpage, size: "92% auto", position: "center", opacity: 0.26 };
  }

  // --- Consent
  if (pathname.startsWith("/consent")) {
    return { src: BG.consent, size: "cover", position: "center", opacity: 0.28 };
  }

  // --- Public legal pages (Footer)
  if (pathname.startsWith("/public/terms") || pathname.startsWith("/public/faq") || pathname.startsWith("/public/impressum")) {
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

  // --- Content
  if (pathname.startsWith("/blog")) {
    return { src: BG.blog, size: "cover", position: "center", opacity: 0.26 };
  }
  if (pathname.startsWith("/news")) {
    return { src: BG.news, size: "cover", position: "center", opacity: 0.26 };
  }

  // --- Vehicles (more specific first)
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

  // Fallback: kein Bild, nur Basis-Gradient
  return null;
}

export function AppBackdrop(props: { children: ReactNode }) {
  const { pathname } = useLocation();

  const cfg = useMemo(() => pickBackground(pathname), [pathname]);

  const style = useMemo(() => {
    const base: React.CSSProperties = {
      // defaults (auch ohne cfg)
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
      {props.children}
    </div>
  );
}