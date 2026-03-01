import { type CSSProperties, type ReactNode } from "react";
import { type AppGateState, type Role } from "../../lib/appGate";
import { type Route } from "../../lib/appRouting";
import AppGateStatusCard from "./AppGateStatusCard";
import AppScaffoldIntroCard from "./AppScaffoldIntroCard";
import { PublicSiteFooter } from "./PublicSiteShell";

export default function AppScaffoldShell(props: {
  route: Route;
  pageTitle: string;
  appStyle?: CSSProperties;
  gateState: AppGateState;
  actorRole: Role | null;
  children: ReactNode;
}): JSX.Element {
  return (
    <div className="ltc-app ltc-app--plain" style={props.appStyle}>
      <div className="ltc-container ltc-page">
        <h1 className="ltc-h1">{props.pageTitle}</h1>

        <AppScaffoldIntroCard actorRole={props.actorRole} />
        <AppGateStatusCard route={props.route} gateState={props.gateState} />

        {props.children}

        <PublicSiteFooter />
      </div>
    </div>
  );
}
