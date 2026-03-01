import SystemStatePage from "../components/SystemStatePage";
import { Button } from "../components/ui";

export function NotFound404(): JSX.Element {
  return (
    <SystemStatePage
      title="Seite nicht gefunden"
      message="Die angeforderte Seite existiert leider nicht."
      icon="?"
      testId="not-found-ui"
      actions={
        <Button variant="primary" onClick={() => window.location.hash = "#/"}>
          Zur Startseite
        </Button>
      }
    />
  );
}

export default NotFound404;
