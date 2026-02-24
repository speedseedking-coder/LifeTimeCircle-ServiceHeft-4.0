// packages/web/src/lib.auth.ts
import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, extractApiError, isRecord } from "./api";

const TOKEN_KEY = "ltc_auth_token_v1";
const EVT = "ltc_auth_changed";

export function getAuthToken(): string | null {
  try {
    const t = localStorage.getItem(TOKEN_KEY);
    return t && t.trim().length > 0 ? t : null;
  } catch {
    return null;
  }
}

export function setAuthToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new Event(EVT));
}

export function clearAuthToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } finally {
    window.dispatchEvent(new Event(EVT));
  }
}

export function authHeaders(token: string | null): Record<string, string> {
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export type AuthState = {
  isBooting: boolean;
  isAuthed: boolean;
  consentRequired: boolean;
  token: string | null;
  refreshMe: () => Promise<void>;
  logout: () => void;
};

function isConsentRequired(err: unknown): boolean {
  // Contract-tolerant:
  // - "consent_required"
  // - { code: "consent_required" }
  // - { detail: "consent_required" }
  // - { detail: { code: "consent_required" } }
  if (typeof err === "string") return err === "consent_required";

  if (!isRecord(err)) return false;

  // { code: "consent_required" }
  if (typeof err.code === "string" && err.code === "consent_required") return true;

  // { detail: "consent_required" } or { detail: { code: "consent_required" } }
  const detail = (err as Record<string, unknown>).detail;
  if (typeof detail === "string") return detail === "consent_required";
  if (isRecord(detail) && typeof detail.code === "string") return detail.code === "consent_required";

  return false;
}

export function useAuthBoot(): AuthState {
  const ranOnce = useRef(false);

  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [isBooting, setIsBooting] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);
  const [consentRequired, setConsentRequired] = useState(false);

  const refreshMe = useCallback(async () => {
    const t = getAuthToken();
    setToken(t);

    if (!t) {
      setIsAuthed(false);
      setConsentRequired(false);
      return;
    }

    const r = await apiGet("/auth/me", { headers: authHeaders(t) });

    if (r.ok) {
      setIsAuthed(true);
      setConsentRequired(false);
      return;
    }

    // interpret error
    const apiErr = extractApiError(r.body);
    const consent = r.status === 403 && isConsentRequired(apiErr);

    if (consent) {
      setIsAuthed(true); // token is valid but blocked by consent gate
      setConsentRequired(true);
      return;
    }

    // any other auth failure => log out
    setIsAuthed(false);
    setConsentRequired(false);
    clearAuthToken();
    setToken(null);
  }, []);

  const logout = useCallback(() => {
    clearAuthToken();
    setToken(null);
    setIsAuthed(false);
    setConsentRequired(false);
  }, []);

  // Boot: run refreshMe exactly once (also stable under React StrictMode dev double-invoke)
  useEffect(() => {
    if (ranOnce.current) return;
    ranOnce.current = true;

    (async () => {
      setIsBooting(true);
      try {
        await refreshMe();
      } finally {
        setIsBooting(false);
      }
    })();
  }, [refreshMe]);

  // Sync if token changes elsewhere (login page, other tab)
  useEffect(() => {
    const onLocal = () => setToken(getAuthToken());
    const onEvt = () => setToken(getAuthToken());
    const onStorage = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY) setToken(getAuthToken());
    };

    window.addEventListener(EVT, onEvt);
    window.addEventListener("storage", onStorage);
    window.addEventListener("focus", onLocal);

    return () => {
      window.removeEventListener(EVT, onEvt);
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("focus", onLocal);
    };
  }, []);

  return { isBooting, isAuthed, consentRequired, token, refreshMe, logout };
}