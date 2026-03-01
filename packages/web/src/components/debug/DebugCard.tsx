import { type ReactNode } from "react";

export default function DebugCard(props: { title: string; children: ReactNode }): JSX.Element {
  return (
    <section className="ltc-card">
      <div className="ltc-card__title">{props.title}</div>
      {props.children}
    </section>
  );
}
