/**
 * PublicLayout Component
 * Für öffentliche Seiten: Landing, Blog, News, Public-QR, Auth
 * 
 * Beinhaltet: Header (minimal) + Footer mit Legal-Links
 */

import { type ReactNode } from "react";

type PublicLayoutProps = {
  header?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
};

export function PublicLayout({ header, footer, children }: PublicLayoutProps) {
  return (
    <div className="ltc-app ltc-app--plain">
      {header}
      <main className="ltc-main">
        <div className="ltc-container">{children}</div>
      </main>
      {footer}
    </div>
  );
}
