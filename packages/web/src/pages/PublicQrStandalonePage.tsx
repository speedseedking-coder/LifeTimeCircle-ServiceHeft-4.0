import { bgStyle, getBgForRoute } from "../lib/appRouting";
import { PublicQrPage } from "./PublicQrPage";

export default function PublicQrStandalonePage(props: { vehicleId: string }): JSX.Element {
  return (
    <div className="ltc-app ltc-app--plain" style={bgStyle(getBgForRoute({ kind: "publicQr", vehicleId: props.vehicleId }))}>
      <div className="ltc-container ltc-page">
        <div style={{ marginBottom: 12 }}>
          <a className="ltc-link" href="#/">
            ← Zur Frontpage
          </a>
        </div>
        <PublicQrPage vehicleId={props.vehicleId} />
      </div>
    </div>
  );
}
