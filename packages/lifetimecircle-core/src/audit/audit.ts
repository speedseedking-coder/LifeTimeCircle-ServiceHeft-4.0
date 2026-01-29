import { BadRequestError } from "../errors.js";
import type { Role } from "../rbac/roles.js";

/**
 * Policy: docs/policies/AUDIT_SCOPE_AND_ENUMS.md (verbindlich)
 * - Pflichtfelder + Redaction
 * - Actions / Target Types als Enums (Uppercase)
 * - Keine Secrets/OTPs/Magic-Links/Tokens/Dokumentinhalte/Klartext-PII
 */

export type ActorType = "user" | "system";
export type AuditScope = "own" | "org" | "shared" | "public";
export type AuditResult = "success" | "denied" | "error";

export const AUDIT_ACTIONS = [
  // Auth / Consent
  "AUTH_CHALLENGE_CREATED",
  "AUTH_CHALLENGE_VERIFIED",
  "AUTH_CHALLENGE_FAILED",
  "SESSION_CREATED",
  "SESSION_REVOKED",
  "CONSENT_ACCEPTED",
  "CONSENT_REQUIRED_BLOCK",

  // RBAC / Governance
  "ROLE_GRANTED",
  "ROLE_REVOKED",
  "ORG_CREATED",
  "ORG_MEMBERSHIP_REQUESTED",
  "ORG_MEMBERSHIP_APPROVED",
  "ORG_MEMBERSHIP_REVOKED",
  "MODERATOR_ACCREDITED",
  "MODERATOR_REVOKED",

  // Vehicle / Entries
  "VEHICLE_CREATED",
  "VEHICLE_UPDATED",
  "VEHICLE_DELETED",
  "ENTRY_CREATED",
  "ENTRY_UPDATED",
  "ENTRY_VERSION_CREATED",
  "ENTRY_DELETED",

  // Documents / Upload
  "UPLOAD_RECEIVED",
  "UPLOAD_QUARANTINED",
  "UPLOAD_SCANNED_CLEAN",
  "UPLOAD_SCANNED_SUSPICIOUS",
  "UPLOAD_APPROVED",
  "UPLOAD_REJECTED",
  "DOCUMENT_VISIBILITY_CHANGED",

  // Verification
  "VERIFICATION_SET_T1",
  "VERIFICATION_SET_T2",
  "VERIFICATION_SET_T3",
  "VERIFICATION_REVOKED",
  "T3_PARTNER_ACCREDITED",
  "T3_PARTNER_REVOKED",

  // Public / Transfer / Sale
  "PUBLIC_SHARE_ENABLED",
  "PUBLIC_SHARE_DISABLED",
  "PUBLIC_SHARE_ROTATED",
  "HANDOVER_TOKEN_CREATED",
  "HANDOVER_COMPLETED",
  "HANDOVER_EXPIRED",

  // Export
  "EXPORT_REDACTED_REQUESTED",
  "EXPORT_REDACTED_READY",
  "EXPORT_FULL_REQUESTED",
  "EXPORT_FULL_READY",
  "EXPORT_DENIED",

  // Admin Ops
  "ADMIN_STEP_UP_SUCCESS",
  "ADMIN_STEP_UP_FAILED",
  "CONFIG_CHANGED",
  "RETENTION_OVERRIDE_SET"
] as const;

export type AuditAction = typeof AUDIT_ACTIONS[number];

export const TARGET_TYPES = [
  "USER",
  "ORG",
  "ORG_MEMBERSHIP",
  "VEHICLE",
  "ENTRY",
  "ENTRY_VERSION",
  "DOCUMENT",
  "VERIFICATION",
  "PUBLIC_SHARE",
  "HANDOVER",
  "EXPORT_JOB",
  "BLOG_POST",
  "NEWSLETTER_SUBSCRIPTION",
  "SYSTEM_CONFIG"
] as const;

export type TargetType = typeof TARGET_TYPES[number];

export const REASON_CODES = ["RBAC_DENY", "CONSENT_MISSING", "QUARANTINE_BLOCK", "RATE_LIMIT", "STEP_UP_REQUIRED"] as const;
export type ReasonCode = typeof REASON_CODES[number];

export interface AuditEvent {
  event_id: string; // UUID
  created_at: string; // UTC ISO
  actor_type: ActorType;
  actor_id: string; // interne ID (kein Klartext-PII)
  actor_role: Role; // Snapshot
  action: AuditAction;

  target_type: TargetType;
  target_id?: string; // intern, optional

  scope: AuditScope;
  result: AuditResult;

  request_id: string;
  correlation_id?: string;

  reason_code?: ReasonCode;

  redacted_metadata?: Record<string, string | number | boolean | null>;
}

function isIsoDateString(s: string): boolean {
  return typeof s === "string" && !Number.isNaN(Date.parse(s));
}

function isProbablyUuid(s: string): boolean {
  // tolerant, damit ihr UUIDv4/v7 später problemlos nutzen könnt
  return typeof s === "string" && s.length >= 16 && /^[0-9a-fA-F-]+$/.test(s);
}

const DISALLOWED_META_KEYS = new Set([
  // PII / identifiers
  "email",
  "phone",
  "name",
  "address",
  "vin",
  "wid",
  "ip",
  "userAgent",
  // auth secrets / tokens
  "otp",
  "code",
  "token",
  "magicLink",
  "password",
  "accessToken",
  "refreshToken",
  // document content hints
  "document_name",
  "filename",
  "file_name",
  "title",
  "content",
  "body"
]);

function sanitizeMetadata(meta?: Record<string, unknown>): Record<string, string | number | boolean | null> | undefined {
  if (!meta) return undefined;

  const out: Record<string, string | number | boolean | null> = {};

  for (const [k, v] of Object.entries(meta)) {
    if (!k || k.trim().length === 0) continue;
    if (DISALLOWED_META_KEYS.has(k)) continue;

    if (typeof v === "string") {
      const s = v.trim();
      // harte Kürzung, um „versehentliche Dumps“ zu verhindern
      if (s.length === 0) continue;
      if (s.length > 120) continue;
      // einfache Email-Erkennung blocken (anti PII)
      if (/@/.test(s)) continue;
      out[k] = s;
      continue;
    }

    if (typeof v === "number" || typeof v === "boolean" || v === null) {
      out[k] = v;
      continue;
    }
  }

  return Object.keys(out).length ? out : undefined;
}

export function buildAuditEvent(input: AuditEvent & { redacted_metadata?: Record<string, unknown> }): AuditEvent {
  if (!isProbablyUuid(input.event_id)) throw new BadRequestError("AuditEvent.event_id ungültig.");
  if (!isIsoDateString(input.created_at)) throw new BadRequestError("AuditEvent.created_at ungültig.");

  if (input.actor_type !== "user" && input.actor_type !== "system") throw new BadRequestError("AuditEvent.actor_type ungültig.");
  if (!input.actor_id || input.actor_id.trim().length === 0) throw new BadRequestError("AuditEvent.actor_id fehlt.");
  if (!input.actor_role) throw new BadRequestError("AuditEvent.actor_role fehlt.");

  if (!AUDIT_ACTIONS.includes(input.action)) throw new BadRequestError("AuditEvent.action ungültig.");
  if (!TARGET_TYPES.includes(input.target_type)) throw new BadRequestError("AuditEvent.target_type ungültig.");

  if (!input.scope) throw new BadRequestError("AuditEvent.scope fehlt.");
  if (!input.result) throw new BadRequestError("AuditEvent.result fehlt.");

  if (!input.request_id || input.request_id.trim().length === 0) throw new BadRequestError("AuditEvent.request_id fehlt.");

  if (input.reason_code && !REASON_CODES.includes(input.reason_code)) {
    throw new BadRequestError("AuditEvent.reason_code ungültig.");
  }

  const e: AuditEvent = {
    event_id: input.event_id,
    created_at: input.created_at,
    actor_type: input.actor_type,
    actor_id: input.actor_id,
    actor_role: input.actor_role,
    action: input.action,
    target_type: input.target_type,
    scope: input.scope,
    result: input.result,
    request_id: input.request_id
  };

  if (input.target_id) e.target_id = input.target_id;
  if (input.correlation_id) e.correlation_id = input.correlation_id;
  if (input.reason_code) e.reason_code = input.reason_code;

  const meta = sanitizeMetadata(input.redacted_metadata);
  if (meta) e.redacted_metadata = meta;

  return e;
}
