/**
 * Checkbox Component
 */

import { type InputHTMLAttributes } from "react";

type CheckboxProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

export function Checkbox({
  label,
  error,
  className = "",
  ...props
}: CheckboxProps) {
  return (
    <div className="ltc-checkbox-wrapper">
      <label className="ltc-checkbox-label">
        <input
          type="checkbox"
          className={`ltc-checkbox ${className}`.trim()}
          {...props}
        />
        {label}
      </label>
      {error ? <div className="ltc-checkbox-error">{error}</div> : null}
    </div>
  );
}
