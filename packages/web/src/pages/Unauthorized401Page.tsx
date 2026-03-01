import SystemStatePage from "../components/SystemStatePage";
import { Button } from "../components/ui";

type Unauthorized401Props = {
  onLoginClick?: () => void;
};

export function Unauthorized401({ onLoginClick }: Unauthorized401Props): JSX.Element {
  const handleLogin = () => {
    window.location.hash = "#/auth";
    onLoginClick?.();
  };

  return (
    <SystemStatePage
      title="Anmeldung erforderlich"
      message="Du musst dich anmelden, um auf diese Seite zuzugreifen."
      icon="Login"
      testId="unauthorized-ui"
      actions={
        <>
          <Button variant="primary" onClick={handleLogin}>
            Anmelden
          </Button>
          <Button variant="secondary" onClick={() => window.location.hash = "#/"}>
            Startseite
          </Button>
        </>
      }
    />
  );
}

export default Unauthorized401;
