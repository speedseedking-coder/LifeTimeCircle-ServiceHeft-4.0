/**
 * Button Component
 * Typen: primary (brand), secondary (neutral), danger (error), ghost
 * Größen: sm, base, lg
 */

import { type ReactNode, type HTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type ButtonSize = "sm" | "base" | "lg";

type ButtonProps = HTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  children: ReactNode;
  type?: "button" | "submit" | "reset";
};

export function Button({
  variant = "primary",
  size = "base",
  disabled = false,
  loading = false,
  children,
  className = "",
  ...props
}: ButtonProps) {
  const cls = `ltc-button ltc-button--${variant} ltc-button--${size}${disabled || loading ? " ltc-button--disabled" : ""}`;

  return (
    <button
      className={`${cls} ${className}`.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <span className="ltc-button__spinner" /> : null}
      {children}
    </button>
  );
}
