import { type ReactNode } from "react";
import { Card } from "./ui";

export default function SystemStatePage(props: {
  title: string;
  message: string;
  icon: ReactNode;
  testId?: string;
  actions?: ReactNode;
}): JSX.Element {
  return (
    <div
      className="ltc-system-error"
      data-testid={props.testId}
      style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--ltc-space-4)" }}
    >
      <Card>
        <div style={{ textAlign: "center", maxWidth: "400px" }}>
          <div style={{ fontSize: "48px", marginBottom: "var(--ltc-space-4)" }}>{props.icon}</div>
          <h1 style={{ fontSize: "var(--ltc-h2-size)" }}>{props.title}</h1>
          <p style={{ color: "var(--ltc-color-text-secondary)", margin: "var(--ltc-space-4) 0" }}>{props.message}</p>
          <div style={{ display: "flex", gap: "var(--ltc-space-3)", justifyContent: "center", marginTop: "var(--ltc-space-6)" }}>
            {props.actions}
          </div>
        </div>
      </Card>
    </div>
  );
}
