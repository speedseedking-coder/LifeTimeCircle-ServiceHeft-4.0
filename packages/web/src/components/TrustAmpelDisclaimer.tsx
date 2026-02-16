import type { CSSProperties } from "react";

const box: CSSProperties = {
  border: "1px solid rgba(0,0,0,0.12)",
  borderRadius: 10,
  padding: 12,
  background: "rgba(0,0,0,0.02)",
};

const text: CSSProperties = {
  margin: 0,
  lineHeight: 1.45,
};

export function TrustAmpelDisclaimer() {
  return (
    <section style={box} aria-label="Trust-Ampel Hinweis">
      <p style={text}>
        „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
      </p>
    </section>
  );
}
