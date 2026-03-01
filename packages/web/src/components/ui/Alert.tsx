/**
 * Alert Component
 * Informational, warning, error, or success messages
 */

import { type HTMLAttributes, type ReactNode } from "react";

export type AlertVariant = "info" | "success" | "warning" | "error";

type AlertProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  variant?: AlertVariant;
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
};

export function Alert({
  children,
  variant = "info",
  title,
  dismissible = false,
  onDismiss,
  className = "",
  ...props
}: AlertProps) {
  const cls = `ltc-alert ltc-alert--${variant}`;

  return (
    <div className={`${cls} ${className}`.trim()} role="alert" {...props}>
      {title ? <div className="ltc-alert-title">{title}</div> : null}
      <div className="ltc-alert-content">{children}</div>
      {dismissible ? (
        <button
          className="ltc-alert-close"
          onClick={onDismiss}
          aria-label="Close alert"
          type="button"
        >
          ✕
        </button>
      ) : null}
    </div>
  );
}
