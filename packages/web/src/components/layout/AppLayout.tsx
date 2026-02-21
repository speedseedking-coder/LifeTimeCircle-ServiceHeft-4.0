import { type CSSProperties, type ReactNode } from "react";
type AppLayoutProps = {
  /** "plain" => ltc-app--plain, "hero" => ltc-app--hero (optional, falls später genutzt) */
  variant: "plain" | "hero";
  style?: CSSProperties;
  header?: ReactNode;
  footer?: ReactNode;

  /** Wenn gesetzt: children werden in ltc-container + optionaler Zusatzklasse gerendert */
  container?: boolean;
  containerClassName?: string;

  children: ReactNode;
};

export function AppLayout(props: AppLayoutProps) {
  const cls = `ltc-app ltc-app--${props.variant}`;

  return (
    <div className={cls} style={props.style}>
      {props.header ? props.header : null}

      {props.container ? (
        <div className={`ltc-container ${props.containerClassName ?? ""}`.trim()}>{props.children}</div>
      ) : (
        props.children
      )}

      {props.footer ? props.footer : null}
    </div>
  );
}