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
    <div className="ltc-system-error" data-testid={props.testId}>
      <Card>
        <div className="ltc-system-error__card">
          <div className="ltc-system-error__icon">{props.icon}</div>
          <h1 className="ltc-system-error__title">{props.title}</h1>
          <p className="ltc-system-error__message">{props.message}</p>
          <div className="ltc-system-error__actions">{props.actions}</div>
        </div>
      </Card>
    </div>
  );
}
