import { type NonModeratorRole, type Role, ROLE_NAV } from "../../lib/appGate";

export default function AppScaffoldIntroCard(props: { actorRole: Role | null }): JSX.Element {
  return (
    <div className="ltc-card">
      <div className="ltc-muted">
        Scaffold/Debug Container. Produktseiten liegen in <code>packages/web/src/pages/*</code>.
      </div>

      <div style={{ marginTop: 12 }}>
        <a className="ltc-link" href="#/">
          ← Zur Frontpage
        </a>
        {import.meta.env.DEV && (
          <>
            {" "}
            ·{" "}
            <a className="ltc-link" href="#/debug/public-site">
              Debug Public Site
            </a>
          </>
        )}
      </div>

      {props.actorRole && props.actorRole !== "moderator" && (
        <div style={{ marginTop: 12 }}>
          <strong>App-Navigation</strong>
          <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
            {ROLE_NAV[props.actorRole as NonModeratorRole].map((item) => (
              <a key={item.href} className="ltc-link" href={item.href}>
                {item.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
