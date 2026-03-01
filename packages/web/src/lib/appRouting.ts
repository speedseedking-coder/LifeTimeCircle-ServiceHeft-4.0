import { type CSSProperties } from "react";

// feature toggles; flip boolean when editorial content is ready or tests require access
export const FEATURES = {
  blogNews: false, // disables blog/news routes when false (kept for future use)
} as const;

export type Route =
  | { kind: "home" }
  | { kind: "notFound" }
  | { kind: "entry" }
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
  | { kind: "onboarding" }
  | { kind: "admin" }
  | { kind: "trustFolders" }
  | { kind: "trustFolderDetail"; folderId: string }
  | { kind: "contact" };

export type BgCfg = {
  url: string;
  opacity: number;
  size?: string;
  position?: string;
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
  jobs: "/images/jobs.png",
  contact: "/images/contact.png",
  news: "/images/news.png",
} as const;

export const DIRECT_PUBLIC_ROUTE_KINDS: ReadonlySet<Route["kind"]> = new Set([
  "home",
  "entry",
  "faq",
  "cookies",
  "jobs",
  "contact",
  "impressum",
  "datenschutz",
]);

export function parseHash(rawHash: string): Route {
  const raw = rawHash.replace(/^#\/?/, "");
  const pathOnly = raw.split("?")[0] ?? "";
  const parts = pathOnly.split("/").filter(Boolean);

  if (parts.length === 0) return { kind: "home" };

  if (parts[0] === "public" && parts[1] === "site") return { kind: "home" };

  if (parts[0] === "qr" && parts[1]) return { kind: "publicQr", vehicleId: parts[1] };
  if (parts[0] === "public" && parts[1] === "qr" && parts[2]) return { kind: "publicQr", vehicleId: parts[2] };

  if (parts[0] === "debug" && parts[1] === "public-site") return { kind: "debugPublicSite" };

  if (parts[0] === "entry") return { kind: "entry" };
  if (parts[0] === "faq") return { kind: "faq" };
  if (parts[0] === "cookies") return { kind: "cookies" };
  if (parts[0] === "jobs") return { kind: "jobs" };
  if (parts[0] === "impressum") return { kind: "impressum" };
  if (parts[0] === "datenschutz") return { kind: "datenschutz" };

  if (FEATURES.blogNews) {
    if (parts[0] === "blog" && parts.length === 1) return { kind: "blogList" };
    if (parts[0] === "blog" && parts[1]) return { kind: "blogPost", slug: parts[1] };
    if (parts[0] === "news" && parts.length === 1) return { kind: "newsList" };
    if (parts[0] === "news" && parts[1]) return { kind: "newsPost", slug: parts[1] };
  }

  if (parts[0] === "auth") return { kind: "auth" };
  if (parts[0] === "consent") return { kind: "consent" };
  if (parts[0] === "contact") return { kind: "contact" };
  if (parts[0] === "vehicles" && parts.length === 1) return { kind: "vehicles" };
  if (parts[0] === "vehicles" && parts[1]) return { kind: "vehicleDetail", vehicleId: parts[1] };
  if (parts[0] === "documents") return { kind: "documents" };
  if (parts[0] === "onboarding") return { kind: "onboarding" };
  if (parts[0] === "admin") return { kind: "admin" };
  if (parts[0] === "trust-folders" && parts.length === 1) return { kind: "trustFolders" };
  if (parts[0] === "trust-folders" && parts[1]) return { kind: "trustFolderDetail", folderId: parts[1] };

  return { kind: "notFound" };
}

export function getPathQrVehicleId(pathname: string): string | null {
  const match = pathname.match(/^\/qr\/([^/?#]+)$/) ?? pathname.match(/^\/public\/qr\/([^/?#]+)$/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function getBgForRoute(route: Route): BgCfg | null {
  switch (route.kind) {
    case "home":
    case "notFound":
      return null;
    case "entry":
      return { url: BG.frontpage2, opacity: 0.22, size: "cover", position: "center" };
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
    case "contact":
      return { url: BG.contact, opacity: 0.24, size: "contain", position: "center top" };
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
    case "admin":
      return { url: BG.rechnungspruefer, opacity: 0.2, size: "cover", position: "center" };
    case "trustFolders":
    case "trustFolderDetail":
      return { url: BG.serviceheft, opacity: 0.2, size: "cover", position: "center" };
    case "debugPublicSite":
      return { url: BG.frontpage2, opacity: 0.14, size: "cover", position: "center" };
  }
}

export function bgStyle(bg: BgCfg | null): CSSProperties {
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

export function getPageTitle(route: Route): string {
  switch (route.kind) {
    case "home":
      return "LifeTimeCircle – ServiceHeft 4.0";
    case "notFound":
      return "404";
    case "entry":
      return "Eintritt";
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
    case "contact":
      return "Contact";
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
    case "admin":
      return "Admin";
    case "trustFolders":
      return "Trust Folders";
    case "trustFolderDetail":
      return `Trust Folder: ${route.folderId}`;
  }
}

export function isDirectPublicRoute(route: Route): boolean {
  return DIRECT_PUBLIC_ROUTE_KINDS.has(route.kind);
}
