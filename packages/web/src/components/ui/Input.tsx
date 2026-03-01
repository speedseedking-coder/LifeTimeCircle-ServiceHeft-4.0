/**
 * Input Component
 * Text-based input with validation states
 */

import { type InputHTMLAttributes, type ReactNode } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
  hint?: string;
  icon?: ReactNode;
  loading?: boolean;
};

export function Input({
  label,
  error,
  hint,
  icon,
  loading = false,
  className = "",
  disabled = false,
  ...props
}: InputProps) {
  const inputCls = `ltc-input ${error ? "ltc-input--error" : ""}${loading ? " ltc-input--loading" : ""}`;

  return (
    <div className="ltc-input-wrapper">
      {label ? (
        <label className="ltc-input-label">
          {label}
          {props.required ? <span className="ltc-required">*</span> : null}
        </label>
      ) : null}
      <div className="ltc-input-container">
        {icon ? <div className="ltc-input-icon">{icon}</div> : null}
        <input
          className={`${inputCls} ${className}`.trim()}
          disabled={disabled || loading}
          {...props}
        />
      </div>
      {error ? <div className="ltc-input-error">{error}</div> : null}
      {hint && !error ? <div className="ltc-input-hint">{hint}</div> : null}
    </div>
  );
}
