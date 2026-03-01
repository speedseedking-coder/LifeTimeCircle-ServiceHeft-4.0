export default function AddonRequiredPanel(props: {
  title?: string;
  message?: string;
  actionHref?: string;
  actionLabel?: string;
}): JSX.Element {
  return (
    <section className="ltc-card ltc-card--compact ltc-section ltc-state-panel ltc-state-panel--warning" role="status" data-testid="addon-required-panel">
      <div className="ltc-state-panel__title">{props.title ?? "Add-on erforderlich"}</div>
      <p className="ltc-state-panel__copy">{props.message ?? "Diese Funktion ist nur mit entsprechendem Add-on verfügbar."}</p>
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
