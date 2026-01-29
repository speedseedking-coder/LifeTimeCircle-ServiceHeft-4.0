export * from "./errors.js";

export * from "./rbac/roles.js";
export * from "./rbac/permissions.js";
export * from "./rbac/policy.js";
export * from "./rbac/vipBusiness.js";

export * from "./privacy/pseudonymize.js";

// Consent: explizit (verhindert TS2308 bei Namenskollisionen)
export type { ConsentDocType, ConsentSource, ConsentRecord } from "./consent/consent.js";
export { assertConsentMeetsRequirements } from "./consent/consent.js";

// Audit: explizit (und ActorType sicherheitshalber aliasen)
export type {
  ActorType as AuditActorType,
  AuditScope,
  AuditResult,
  AuditAction,
  TargetType,
  ReasonCode,
  AuditEvent
} from "./audit/audit.js";
export { AUDIT_ACTIONS, TARGET_TYPES, REASON_CODES, buildAuditEvent } from "./audit/audit.js";

export * from "./publicQr/trustscore.js";
