import { httpFetch } from "./httpFetch";

/**
 * Minimal silent auth boot.
 * - Called once on app start
 * - 401 => redirect
 * - 200 => do nothing (session valid)
 */
export async function bootAuth(): Promise<void> {
  try {
    const res = await httpFetch("/auth/me", {
      method: "GET",
      credentials: "include"
    });

    if (!res.ok && res.status !== 401) {
      // Non-auth errors should not block app
      return;
    }

    // 401 already handled by httpFetch wrapper
  } catch {
    // Network errors should not hard crash boot
  }
}

