/**
 * Minimal, side-effect-only 401 handler.
 * Avoids TS narrowing traps by keeping logic in one place.
 */
export function handleUnauthorized(): void {
  try {
    // Clear common auth storage keys (adjust if your app uses different ones)
    localStorage.removeItem("ltc_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.removeItem("ltc_token");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
  } catch {
    // ignore storage errors (private mode, denied, etc.)
  }

  // Hard redirect to login (prevents SPA state inconsistencies)
  if (typeof window !== "undefined") {
    const current = window.location.pathname + window.location.search + window.location.hash;
    const next = encodeURIComponent(current);
    window.location.assign(`/login?next=${next}`);
  }
}
