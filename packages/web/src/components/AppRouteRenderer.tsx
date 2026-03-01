import AppScaffoldShell from "./layout/AppScaffoldShell";
import { type AppGateState, type Role } from "../lib/appGate";
import { bgStyle, getBgForRoute, isDirectPublicRoute, type Route } from "../lib/appRouting";
import AppScaffoldContent from "./AppScaffoldContent";
import PublicRouteRenderer from "./PublicRouteRenderer";
import NotFound404 from "../pages/NotFound404Page";

export default function AppRouteRenderer(props: {
  route: Route;
  pageTitle: string;
  actorRole: Role | null;
  gateState: AppGateState;
}): JSX.Element | null {
  if (props.route.kind === "notFound") {
    return <NotFound404 />;
  }

  if (isDirectPublicRoute(props.route)) {
    return <PublicRouteRenderer route={props.route as Extract<Route, { kind: "home" | "entry" | "faq" | "cookies" | "jobs" | "contact" | "impressum" | "datenschutz" }>} />;
  }

  return (
    <AppScaffoldShell
      route={props.route}
      pageTitle={props.pageTitle}
      appStyle={bgStyle(getBgForRoute(props.route))}
      gateState={props.gateState}
      actorRole={props.actorRole}
    >
      <AppScaffoldContent route={props.route} actorRole={props.actorRole} gateState={props.gateState} />
    </AppScaffoldShell>
  );
}
