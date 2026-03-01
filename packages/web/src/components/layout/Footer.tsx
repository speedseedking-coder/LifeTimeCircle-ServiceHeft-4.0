/**
 * Footer Component
 * Standard Footer mit Legal-Links
 */

import { type ReactNode } from "react";

type FooterProps = {
  children?: ReactNode;
};

export function Footer({ children }: FooterProps) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="ltc-footer">
      <div className="ltc-container">
        {children && <div className="ltc-footer-content">{children}</div>}
        <div className="ltc-footer-bottom">
          <div>
            © {currentYear} LifeTimeCircle. Alle Rechte vorbehalten.
          </div>
          <div style={{ display: "flex", gap: "var(--ltc-space-4)", fontSize: "var(--ltc-text-sm)" }}>
            <a href="#/impressum">Impressum</a>
            <a href="#/datenschutz">Datenschutz</a>
            <a href="#/cookies">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
