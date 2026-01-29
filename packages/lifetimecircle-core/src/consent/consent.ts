import { BadRequestError } from "../errors.js";

export type ConsentDocType = "terms" | "privacy";
export type ConsentSource = "ui" | "api";

export interface ConsentRecord {
  user_id: string; // interne ID
  doc_type: ConsentDocType;
  doc_version: string;
  accepted_at: string; // ISO
  source: ConsentSource;

  // optional (keine Klartext-PII)
  ip_hmac?: string;
  user_agent_hmac?: string;
  evidence_hash?: string;
}

function isIsoDateString(s: string): boolean {
  return typeof s === "string" && !Number.isNaN(Date.parse(s));
}

function assertRecord(r: ConsentRecord): void {
  if (!r) throw new BadRequestError("ConsentRecord fehlt.");
  if (!r.user_id || r.user_id.trim().length === 0) throw new BadRequestError("ConsentRecord.user_id fehlt.");
  if (r.doc_type !== "terms" && r.doc_type !== "privacy") throw new BadRequestError("ConsentRecord.doc_type ungültig.");
  if (!r.doc_version || r.doc_version.trim().length === 0) throw new BadRequestError("ConsentRecord.doc_version fehlt.");
  if (!isIsoDateString(r.accepted_at)) throw new BadRequestError("ConsentRecord.accepted_at ungültig.");
  if (r.source !== "ui" && r.source !== "api") throw new BadRequestError("ConsentRecord.source ungültig.");
  if (r.ip_hmac && r.ip_hmac.trim().length < 16) throw new BadRequestError("ConsentRecord.ip_hmac zu kurz.");
  if (r.user_agent_hmac && r.user_agent_hmac.trim().length < 16) throw new BadRequestError("ConsentRecord.user_agent_hmac zu kurz.");
  if (r.evidence_hash && r.evidence_hash.trim().length < 16) throw new BadRequestError("ConsentRecord.evidence_hash zu kurz.");
}

export function assertConsentMeetsRequirements(
  records: ConsentRecord[],
  requiredVersions: Record<ConsentDocType, string>
): void {
  if (!records || !Array.isArray(records)) throw new BadRequestError("ConsentRecords fehlen.");

  const termsReq = requiredVersions.terms;
  const privacyReq = requiredVersions.privacy;
  if (!termsReq || !privacyReq) throw new BadRequestError("requiredVersions unvollständig (terms/privacy).");

  for (const r of records) assertRecord(r);

  const terms = records.find((r) => r.doc_type === "terms" && r.doc_version === termsReq);
  const privacy = records.find((r) => r.doc_type === "privacy" && r.doc_version === privacyReq);

  if (!terms) throw new BadRequestError("Consent fehlt: terms (required version).");
  if (!privacy) throw new BadRequestError("Consent fehlt: privacy (required version).");
}
