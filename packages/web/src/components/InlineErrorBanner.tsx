export default function InlineErrorBanner(props: { message: string }): JSX.Element {
  return (
    <div className="ltc-card" role="alert" style={{ borderColor: "rgba(255,120,120,0.6)", marginTop: 12 }}>
      <div className="ltc-card__title">Fehler</div>
      <div className="ltc-muted">{props.message}</div>
    </div>
  );
}