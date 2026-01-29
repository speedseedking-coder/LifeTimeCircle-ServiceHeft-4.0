import crypto from "node:crypto";
import { BadRequestError } from "../errors.js";

/**
 * Policy AUTH_SECURITY_DEFAULTS.md / CRYPTO_STANDARDS.md:
 * - E-Mail Normalisierung: trim + lowercase + Unicode NFKC
 * - HMAC-SHA256 für email_hmac, token_hash, otp_hash, log-safe identifiers
 * - Nie OTP/Magic-Link im Klartext persistieren/loggen
 */

const ENV_KEYS = ["LTC_PSEUDONYM_HMAC_KEY", "LIFETIMECIRCLE_HMAC_KEY", "LTC_HMAC_KEY"] as const;

export function getHmacKeyFromEnv(): string {
  for (const k of ENV_KEYS) {
    const v = process.env[k];
    if (typeof v === "string" && v.trim().length >= 32) return v.trim();
  }
  throw new BadRequestError("HMAC-Key fehlt/zu kurz. Setze ENV LTC_PSEUDONYM_HMAC_KEY (mind. 32 Zeichen).");
}

export function normalizeEmail(email: string): string {
  if (typeof email !== "string") throw new BadRequestError("normalizeEmail: email ungültig.");
  // Trim, lowercase, Unicode-Normalisierung (NFKC)
  return email.trim().toLowerCase().normalize("NFKC");
}

function hmacSha256Base64Url(value: string, hmacKey: string): string {
  if (!value || value.trim().length === 0) throw new BadRequestError("HMAC: value leer.");
  if (!hmacKey || hmacKey.trim().length < 32) throw new BadRequestError("HMAC: hmacKey zu kurz.");
  return crypto.createHmac("sha256", hmacKey).update(value, "utf8").digest("base64url");
}

/**
 * Pseudonymisierung (log-safe identifier), stabil, nicht reversibel ohne Key.
 * Output: base64url.
 */
export function hmacPseudonymize(value: string, hmacKey: string): string {
  return hmacSha256Base64Url(value, hmacKey);
}

/**
 * email_hmac = HMAC-SHA256(app_secret, email_normalized)
 */
export function emailHmac(email: string, hmacKey: string): string {
  const norm = normalizeEmail(email);
  return hmacSha256Base64Url(norm, hmacKey);
}

/**
 * otp_hash = HMAC-SHA256(secret, otp + challenge_id)
 * -> kein Klartext-OTP in DB/Logs
 */
export function otpHash(otp: string, challengeId: string, hmacKey: string): string {
  if (!otp || otp.trim().length === 0) throw new BadRequestError("otpHash: otp leer.");
  if (!challengeId || challengeId.trim().length === 0) throw new BadRequestError("otpHash: challengeId leer.");
  return hmacSha256Base64Url(`${otp}${challengeId}`, hmacKey);
}

/**
 * token_hash = HMAC-SHA256(secret, raw_token)
 * -> kein Klartext-Token in DB/Logs
 */
export function tokenHash(rawToken: string, hmacKey: string): string {
  if (!rawToken || rawToken.trim().length === 0) throw new BadRequestError("tokenHash: rawToken leer.");
  return hmacSha256Base64Url(rawToken, hmacKey);
}

/**
 * Convenience: log-safe Pseudonyme für häufige Felder
 */
export function pseudonymizeEmail(email: string, hmacKey: string): string {
  return hmacSha256Base64Url(`email:${normalizeEmail(email)}`, hmacKey);
}

export function pseudonymizeIp(ip: string, hmacKey: string): string {
  if (!ip || ip.trim().length === 0) throw new BadRequestError("pseudonymizeIp: ip leer.");
  return hmacSha256Base64Url(`ip:${ip.trim()}`, hmacKey);
}

export function pseudonymizeUserAgent(ua: string, hmacKey: string): string {
  if (!ua || ua.trim().length === 0) throw new BadRequestError("pseudonymizeUserAgent: ua leer.");
  return hmacSha256Base64Url(`ua:${ua.trim()}`, hmacKey);
}
