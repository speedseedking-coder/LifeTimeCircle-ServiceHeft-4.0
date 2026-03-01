// packages/web/src/App.tsx
import { useEffect, useMemo } from "react";
import AppRouteRenderer from "./components/AppRouteRenderer";
import { useHash } from "./hooks/useHash";
import { useAppGate } from "./hooks/useAppGate";
import {
  getPageTitle,
  getPathQrVehicleId,
  parseHash,
  type Route,
} from "./lib/appRouting";
import PublicQrStandalonePage from "./pages/PublicQrStandalonePage";

/** ---------------------------
 * App Root
 * --------------------------- */
export default function App() {
  const pathQrVehicleId = getPathQrVehicleId(window.location.pathname);
  if (pathQrVehicleId) {
    return <PublicQrStandalonePage vehicleId={pathQrVehicleId} />;
  }

  const hash = useHash();
  const route = useMemo<Route>(() => parseHash(hash), [hash]);
  const { actorRole, gateState } = useAppGate(route);

  useEffect(() => {
    const raw = (window.location.hash || "").replace(/^#\/?/, "");
    if (raw.startsWith("public/site")) window.location.replace("#/");
  }, [route.kind]);

  const pageTitle = useMemo(() => getPageTitle(route), [route]);

  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);

  return (
    <AppRouteRenderer
      route={route}
      pageTitle={pageTitle}
      actorRole={actorRole}
      gateState={gateState}
    />
  );
}
