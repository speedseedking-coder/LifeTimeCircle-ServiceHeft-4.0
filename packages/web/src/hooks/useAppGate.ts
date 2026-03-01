import { useEffect, useState } from "react";
import { apiGet, isRecord } from "../api";
import { authHeaders, getAuthToken } from "../lib.auth";
import {
  canAccessRouteByRole,
  isConsentRequiredBody,
  isGuardedRoute,
  roleFromMe,
  safeNextHash,
  type AppGateState,
  type Role,
} from "../lib/appGate";
import { type Route } from "../lib/appRouting";

export function useAppGate(route: Route): { actorRole: Role | null; gateState: AppGateState } {
  const [gateState, setGateState] = useState<AppGateState>(() => (isGuardedRoute(route) ? "loading" : "ready"));
  const [actorRole, setActorRole] = useState<Role | null>(null);

  useEffect(() => {
    let active = true;

    if (!isGuardedRoute(route)) {
      setGateState("ready");
      return () => {
        active = false;
      };
    }

    const token = getAuthToken();
    if (!token) {
      setActorRole(null);
      setGateState("unauth");
      return () => {
        active = false;
      };
    }

    setGateState("loading");
    const headers = authHeaders(token);

    apiGet("/auth/me", { headers }).then((response) => {
      if (!active) return;

      if (!response.ok) {
        if (response.status === 401) {
          setActorRole(null);
          setGateState("unauth");
          return;
        }
        if (response.status === 403 && isConsentRequiredBody(response.body)) {
          setActorRole(null);
          setGateState("consent_required");
          return;
        }
        setActorRole(null);
        setGateState("forbidden");
        return;
      }

      const role = roleFromMe(response.body);
      setActorRole(role);

      if (role === null) {
        setGateState("forbidden");
        return;
      }

      if (route.kind === "consent") {
        setGateState("ready");
        return;
      }

      if (!canAccessRouteByRole(route, role)) {
        setGateState("forbidden");
        return;
      }

      apiGet("/consent/status", { headers }).then((consentResponse) => {
        if (!active) return;

        if (!consentResponse.ok) {
          if (consentResponse.status === 401) {
            setGateState("unauth");
            return;
          }
          if (consentResponse.status === 403 && isConsentRequiredBody(consentResponse.body)) {
            setGateState("consent_required");
            return;
          }
          setGateState("forbidden");
          return;
        }

        if (!isRecord(consentResponse.body) || consentResponse.body.is_complete !== true) {
          setGateState("consent_required");
          return;
        }

        setGateState("ready");
      });
    });

    return () => {
      active = false;
    };
  }, [route]);

  useEffect(() => {
    if (!isGuardedRoute(route)) return;

    if (gateState === "unauth") {
      if ((window.location.hash || "").startsWith("#/auth")) return;
      const next = encodeURIComponent(safeNextHash(window.location.hash || "#/"));
      window.location.hash = `#/auth?next=${next}`;
      return;
    }

    if (gateState === "consent_required" && route.kind !== "consent") {
      const next = encodeURIComponent(safeNextHash(window.location.hash || "#/vehicles"));
      window.location.hash = `#/consent?next=${next}`;
    }
  }, [gateState, route]);

  return { actorRole, gateState };
}
