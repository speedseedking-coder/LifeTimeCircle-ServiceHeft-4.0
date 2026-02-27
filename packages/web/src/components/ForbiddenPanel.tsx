export default function ForbiddenPanel(): JSX.Element {
  return (
    <div className="ltc-card" role="status" style={{ marginTop: 12 }}>
      <div className="ltc-card__title">Kein Zugriff</div>
      <div className="ltc-muted">Du hast keine Berechtigung für diese Aktion.</div>
    </div>
  );
}