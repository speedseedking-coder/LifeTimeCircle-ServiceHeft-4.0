/**
 * Minimal, side-effect-only 401 handler.
 * Keeps redirect logic centralized and hash-router compatible.
 *
 * Rules:
 * - Hash routing: redirect to "#/auth?next=..."
 * - next is derived from current hash (incl. leading "#")
 * - Loop guard: if already on "#/auth", do nothing
 * - No typographic unicode characters (ASCII only)
 */
export function handleUnauthorized(): void {
  try {
    // Clear common auth storage keys (adjust if your app uses different ones)
    localStorage.removeItem("ltc_auth_token_v1");
    localStorage.removeItem("ltc_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.removeItem("ltc_auth_token_v1");
    sessionStorage.removeItem("ltc_token");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
  } catch {
    // ignore storage errors (private mode, denied, etc.)
  }

  if (typeof window === "undefined") return;

  const hash = window.location.hash || "#/";
  // Loop guard: if we are already on auth route, do not rewrite hash again.
  // Accept both "#/auth" and "#/auth?next=..."
  if (hash.startsWith("#/auth")) return;

  const next = encodeURIComponent(hash);
  window.location.hash = `#/auth?next=${next}`;
}
