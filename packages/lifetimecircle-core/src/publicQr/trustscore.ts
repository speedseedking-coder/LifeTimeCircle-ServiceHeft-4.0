/**
 * Public-QR Trustscore:
 * - bewertet ausschließlich Nachweis-/Dokumentationsqualität
 * - bewertet NICHT technischen Zustand
 * - Public Response: keine Metrics/Counts/Percentages/Zeiträume
 */

export type TrafficLight = "rot" | "orange" | "gelb" | "gruen";

/**
 * Pflicht-Disclaimer (Policy, exakte UI Copy):
 * „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität.
 *  Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“
 */
export const PUBLIC_QR_DISCLAIMER =
  "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

export type VerificationPresence = "none" | "t1" | "t2" | "t3";

export interface PublicQrSnapshot {
  hasHistory: boolean;
  verification: VerificationPresence; // zusammengefasster Status
  isRegularlyUpdated: boolean;
  hasAccident: boolean;
  accidentClosedWithEvidence: boolean; // nur relevant, wenn hasAccident
}

export type PublicIndicator =
  | "history_present"
  | "history_missing"
  | "verification_low"
  | "verification_medium"
  | "verification_high"
  | "regularity_ok"
  | "regularity_missing"
  | "accident_none"
  | "accident_closed_with_evidence"
  | "accident_open_or_unproven";

export interface PublicQrResult {
  light: TrafficLight;
  indicators: PublicIndicator[];
  disclaimer: string;
}

function uniq<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}

export function computePublicQrTrust(snapshot: PublicQrSnapshot): PublicQrResult {
  const indicators: PublicIndicator[] = [];

  if (snapshot.hasHistory) indicators.push("history_present");
  else indicators.push("history_missing");

  switch (snapshot.verification) {
    case "t3":
      indicators.push("verification_high");
      break;
    case "t2":
      indicators.push("verification_medium");
      break;
    case "t1":
      indicators.push("verification_low");
      break;
    case "none":
    default:
      indicators.push("verification_low");
      break;
  }

  if (snapshot.isRegularlyUpdated) indicators.push("regularity_ok");
  else indicators.push("regularity_missing");

  if (!snapshot.hasAccident) indicators.push("accident_none");
  else if (snapshot.accidentClosedWithEvidence) indicators.push("accident_closed_with_evidence");
  else indicators.push("accident_open_or_unproven");

  // Ampel-Regeln (ohne Metriken in der Ausgabe)
  const hasGoodVerification = snapshot.verification === "t3" || snapshot.verification === "t2";
  const hasAnyVerification = snapshot.verification !== "none";
  const accidentOk = !snapshot.hasAccident || snapshot.accidentClosedWithEvidence;

  let light: TrafficLight = "rot";

  if (!snapshot.hasHistory) {
    light = "rot";
  } else if (hasGoodVerification && snapshot.isRegularlyUpdated && accidentOk) {
    light = "gruen";
  } else if (hasAnyVerification && accidentOk) {
    light = "gelb";
    if (!snapshot.isRegularlyUpdated || snapshot.verification === "t1") {
      light = "orange";
    }
  } else {
    light = "orange";
  }

  return {
    light,
    indicators: uniq(indicators),
    disclaimer: PUBLIC_QR_DISCLAIMER
  };
}
