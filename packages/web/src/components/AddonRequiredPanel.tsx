export default function AddonRequiredPanel(): JSX.Element {
  return (
    <div className="ltc-card" role="status" style={{ marginTop: 12 }}>
      <div className="ltc-card__title">Add-on erforderlich</div>
      <div className="ltc-muted">Diese Funktion ist nur mit entsprechendem Add-on verfügbar.</div>
    </div>
  );
}