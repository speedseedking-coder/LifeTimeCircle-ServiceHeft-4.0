/**
 * Badge Component
 * Status indicator or tag
 */

import { type HTMLAttributes, type ReactNode } from "react";

export type BadgeVariant = "neutral" | "info" | "success" | "warning" | "error" | "trust-green" | "trust-yellow" | "trust-red" | "trust-gray";

type BadgeProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "base";
};

export function Badge({
  children,
  variant = "neutral",
  size = "base",
  className = "",
  ...props
}: BadgeProps) {
  const cls = `ltc-badge ltc-badge--${variant} ltc-badge--${size}`;

  return (
    <div className={`${cls} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
}
