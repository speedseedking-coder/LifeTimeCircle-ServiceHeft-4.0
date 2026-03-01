/**
 * Card Component
 * Container for grouped content
 */

import { type HTMLAttributes, type ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  hoverable?: boolean;
  interactive?: boolean;
};

export function Card({
  children,
  hoverable = false,
  interactive = false,
  className = "",
  ...props
}: CardProps) {
  const cls = `ltc-card${hoverable ? " ltc-card--hoverable" : ""}${interactive ? " ltc-card--interactive" : ""}`;

  return (
    <div className={`${cls} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
}
