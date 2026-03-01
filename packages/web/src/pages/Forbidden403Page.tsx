import SystemStatePage from "../components/SystemStatePage";
import { Button } from "../components/ui";

type Forbidden403Props = {
  reason?: string;
};

export function Forbidden403({ reason }: Forbidden403Props): JSX.Element {
  return (
    <SystemStatePage
      title="Zugriff verweigert"
      message={reason || "Du hast nicht die erforderlichen Rechte, um auf diese Seite zuzugreifen."}
      icon="403"
      testId="forbidden-ui"
      actions={
        <Button variant="secondary" onClick={() => window.location.hash = "#/"}>
          Zurück zur Startseite
        </Button>
      }
    />
  );
}

export default Forbidden403;
