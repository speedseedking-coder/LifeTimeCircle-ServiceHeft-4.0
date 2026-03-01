/**
 * EmptyState Component
 * Displayed when no data available
 */

import { type ReactNode } from "react";
import { Card } from "./Card";

type EmptyStateProps = {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
};

export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <Card>
      <div className="ltc-empty-state">
        {icon ? <div className="ltc-empty-state-icon">{icon}</div> : null}
        <h3 className="ltc-empty-state-title">{title}</h3>
        {description ? (
          <p className="ltc-empty-state-description">{description}</p>
        ) : null}
        {action ? <div className="ltc-empty-state-action">{action}</div> : null}
      </div>
    </Card>
  );
}
