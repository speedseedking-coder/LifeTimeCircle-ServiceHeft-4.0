export default function InlineErrorBanner(props: { message: string }): JSX.Element {
  return (
    <section className="ltc-card ltc-card--compact ltc-section ltc-state-panel ltc-state-panel--error" role="alert" data-testid="inline-error-banner">
      <div className="ltc-state-panel__title">Fehler</div>
      <p className="ltc-state-panel__copy">{props.message}</p>
    </section>
  );
}
