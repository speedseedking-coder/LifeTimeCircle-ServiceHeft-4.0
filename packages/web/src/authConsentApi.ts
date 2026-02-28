import { apiGet, apiPost, isRecord } from "./api";

export type RequiredConsent = {
  doc_type: "terms" | "privacy";
  doc_version: string;
};

export type ConsentAcceptance = RequiredConsent & {
  accepted_at: string;
  source?: string;
};

type AuthRequestBody = {
  challenge_id?: unknown;
  challengeId?: unknown;
  message?: unknown;
  dev_otp?: unknown;
  devOtp?: unknown;
};

type AuthVerifyBody = {
  access_token?: unknown;
  accessToken?: unknown;
  expires_at?: unknown;
  expiresAt?: unknown;
};

export async function fetchRequiredConsents() {
  return apiGet("/consent/current");
}

export async function requestAuthChallenge(email: string) {
  return apiPost("/auth/request", { email });
}

export async function verifyAuthChallenge(payload: {
  email: string;
  challengeId: string;
  otp: string;
  consents: ConsentAcceptance[];
}) {
  return apiPost("/auth/verify", {
    email: payload.email,
    challenge_id: payload.challengeId,
    otp: payload.otp,
    consents: payload.consents,
  });
}

export async function fetchConsentStatus(headers: Record<string, string>) {
  return apiGet("/consent/status", { headers });
}

export async function acceptRequiredConsents(consents: ConsentAcceptance[], headers: Record<string, string>) {
  return apiPost("/consent/accept", { consents }, { headers });
}

export async function logoutSession(headers: Record<string, string>) {
  return apiPost("/auth/logout", undefined, { headers });
}

export function normalizeRequiredConsents(body: unknown): RequiredConsent[] {
  let docs: unknown = null;

  if (Array.isArray(body)) {
    docs = body;
  } else if (isRecord(body)) {
    for (const key of ["required", "documents", "docs", "consents", "items"]) {
      const candidate = body[key];
      if (Array.isArray(candidate)) {
        docs = candidate;
        break;
      }
    }
  }

  const out: RequiredConsent[] = [];

  if (Array.isArray(docs)) {
    for (const item of docs) {
      if (!isRecord(item)) continue;

      const typeRaw = item.doc_type ?? item.type ?? item.docType ?? item.name;
      const versionRaw = item.doc_version ?? item.version ?? item.docVersion;
      const doc_type = typeRaw === "terms" || typeRaw === "privacy" ? typeRaw : null;
      const doc_version = typeof versionRaw === "string" ? versionRaw.trim() : "";

      if (!doc_type || doc_version.length === 0) continue;
      if (out.some((entry) => entry.doc_type === doc_type)) continue;

      out.push({ doc_type, doc_version });
    }
  }

  if (out.length > 0) return out;

  if (isRecord(body)) {
    for (const doc_type of ["terms", "privacy"] as const) {
      const candidate = body[doc_type];
      if (typeof candidate === "string" && candidate.trim().length > 0) {
        out.push({ doc_type, doc_version: candidate.trim() });
        continue;
      }

      if (isRecord(candidate)) {
        const versionRaw = candidate.version ?? candidate.doc_version;
        if (typeof versionRaw === "string" && versionRaw.trim().length > 0) {
          out.push({ doc_type, doc_version: versionRaw.trim() });
        }
      }
    }
  }

  return out;
}

export function normalizeAcceptedConsents(body: unknown): ConsentAcceptance[] {
  if (!isRecord(body) || !Array.isArray(body.accepted)) return [];

  const out: ConsentAcceptance[] = [];
  for (const item of body.accepted) {
    if (!isRecord(item)) continue;

    const typeRaw = item.doc_type ?? item.type ?? item.docType ?? item.name;
    const versionRaw = item.doc_version ?? item.version ?? item.docVersion;
    const acceptedAtRaw = item.accepted_at ?? item.acceptedAt;
    const sourceRaw = item.source;

    const doc_type = typeRaw === "terms" || typeRaw === "privacy" ? typeRaw : null;
    const doc_version = typeof versionRaw === "string" ? versionRaw.trim() : "";
    const accepted_at = typeof acceptedAtRaw === "string" ? acceptedAtRaw : "";
    const source = typeof sourceRaw === "string" ? sourceRaw : undefined;

    if (!doc_type || doc_version.length === 0 || accepted_at.length === 0) continue;
    out.push({ doc_type, doc_version, accepted_at, source });
  }
  return out;
}

export function readAuthChallenge(body: unknown): { challengeId: string | null; message: string; devOtp: string | null } {
  if (!isRecord(body)) return { challengeId: null, message: "", devOtp: null };
  const data = body as AuthRequestBody;
  return {
    challengeId:
      typeof data.challenge_id === "string"
        ? data.challenge_id
        : typeof data.challengeId === "string"
          ? data.challengeId
          : null,
    message: typeof data.message === "string" ? data.message : "",
    devOtp: typeof data.dev_otp === "string" ? data.dev_otp : typeof data.devOtp === "string" ? data.devOtp : null,
  };
}

export function readVerifiedSession(body: unknown): { accessToken: string | null; expiresAt: string | null } {
  if (!isRecord(body)) return { accessToken: null, expiresAt: null };
  const data = body as AuthVerifyBody;
  return {
    accessToken:
      typeof data.access_token === "string"
        ? data.access_token
        : typeof data.accessToken === "string"
          ? data.accessToken
          : null,
    expiresAt: typeof data.expires_at === "string" ? data.expires_at : typeof data.expiresAt === "string" ? data.expiresAt : null,
  };
}

export function buildConsentAcceptances(required: RequiredConsent[], acceptedAtIso = new Date().toISOString()): ConsentAcceptance[] {
  return required.map((item) => ({
    doc_type: item.doc_type,
    doc_version: item.doc_version,
    accepted_at: acceptedAtIso,
    source: "ui",
  }));
}
