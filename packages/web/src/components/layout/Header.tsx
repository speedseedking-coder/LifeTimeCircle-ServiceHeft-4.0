/**
 * Header Component
 * Für Public-Navigation (Logo + Links)
 */

import { type ReactNode } from "react";

type HeaderProps = {
  logo?: ReactNode;
  nav?: ReactNode;
  actions?: ReactNode;
};

export function Header({ logo, nav, actions }: HeaderProps) {
  return (
    <header className="ltc-header">
      <div className="ltc-container">
        <div className="ltc-header-content">
          <div className="ltc-logo">{logo || "LifeTimeCircle"}</div>
          {nav}
          {actions}
        </div>
      </div>
    </header>
  );
}
