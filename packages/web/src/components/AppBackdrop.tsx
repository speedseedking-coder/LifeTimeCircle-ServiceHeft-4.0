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

type AppBackdropProps = {
  children: ReactNode;
  /** optional: className für Wrapper */
  className?: string;
  /** optional: Inline-Style für Wrapper */
  style?: CSSProperties;
};

/**
 * AppBackdrop: Layout-Wrapper, der Hintergrund + Content-Container liefert.
 * (CSS ist in AppBackdrop.css)
 */
export default function AppBackdrop(props: AppBackdropProps) {
  const pathname = useHashPathname();

  // Page-Key für mögliche transitions / scoping
  const pageKey = useMemo(() => {
    // z.B. "/vehicles/123" -> "/vehicles/:id"
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === "vehicles") return "/vehicles/:id";
    return pathname || "/";
  }, [pathname]);

  return (
    <div className={props.className ?? "ltc-app"} style={props.style} data-page={pageKey}>
      <div className="ltc-bg" aria-hidden="true" />
      <div className="ltc-shell">{props.children}</div>
    </div>
  );
}
