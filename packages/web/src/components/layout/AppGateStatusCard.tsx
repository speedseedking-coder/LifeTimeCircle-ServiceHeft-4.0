import { isGuardedRoute, type AppGateState } from "../../lib/appGate";
import { type Route } from "../../lib/appRouting";
import Forbidden403 from "../../pages/Forbidden403Page";

export default function AppGateStatusCard(props: { route: Route; gateState: AppGateState }): JSX.Element | null {
  if (!isGuardedRoute(props.route)) {
    return null;
  }

  if (props.gateState === "loading") {
    return (
      <div className="ltc-card">
        <div className="ltc-muted">Prüfe Zugriff …</div>
      </div>
    );
  }

  if (props.gateState === "forbidden") {
    return <Forbidden403 reason="Kein Zugriff auf diesen Bereich." />;
  }

  return null;
}
