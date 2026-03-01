export default function ForbiddenPanel(props: {
  title?: string;
  message?: string;
  actionHref?: string;
  actionLabel?: string;
}): JSX.Element {
  return (
    <section className="ltc-card ltc-card--compact ltc-section ltc-state-panel ltc-state-panel--error" role="status" data-testid="forbidden-panel">
      <div className="ltc-state-panel__title">{props.title ?? "Kein Zugriff"}</div>
      <p className="ltc-state-panel__copy">{props.message ?? "Du hast keine Berechtigung für diese Aktion."}</p>
      {props.actionHref && props.actionLabel ? (
        <div className="ltc-state-panel__actions">
          <a className="ltc-link" href={props.actionHref}>
            {props.actionLabel}
          </a>
        </div>
      ) : null}
    </section>
  );
}
