import { useEffect, useState } from "react";
import { apiGet, isRecord } from "../api";
import { authHeaders, getAuthToken } from "../lib.auth";
import {
  canAccessRouteByRole,
  isConsentRequiredBody,
  isGuardedRoute,
  requiresConsentCheck,
  roleFromMe,
  safeNextHash,
  type AppGateState,
  type Role,
} from "../lib/appGate";
import { type Route } from "../lib/appRouting";

function routeGateKey(route: Route): string {
  return JSON.stringify(route);
}

export function useAppGate(route: Route): { actorRole: Role | null; gateState: AppGateState } {
  const guarded = isGuardedRoute(route);
  const currentRouteKey = routeGateKey(route);
  const [gateState, setGateState] = useState<AppGateState>(() => (guarded ? "loading" : "ready"));
  const [actorRole, setActorRole] = useState<Role | null>(null);
  const [resolvedRouteKey, setResolvedRouteKey] = useState<string>(() => (guarded ? "" : currentRouteKey));

  useEffect(() => {
    let active = true;

    const settle = (nextGateState: AppGateState, nextActorRole: Role | null) => {
      if (!active) return;
      setActorRole(nextActorRole);
      setGateState(nextGateState);
      setResolvedRouteKey(currentRouteKey);
    };

    if (!guarded) {
      setGateState("ready");
      setResolvedRouteKey(currentRouteKey);
      return () => {
        active = false;
      };
    }

    const token = getAuthToken();
    if (!token) {
      settle("unauth", null);
      return () => {
        active = false;
      };
    }

    setResolvedRouteKey("");
    setGateState("loading");
    const headers = authHeaders(token);

    apiGet("/auth/me", { headers }).then((response) => {
      if (!active) return;

      if (!response.ok) {
        if (response.status === 401) {
          settle("unauth", null);
          return;
        }
        if (response.status === 403 && isConsentRequiredBody(response.body)) {
          settle("consent_required", null);
          return;
        }
        settle("forbidden", null);
        return;
      }

      const role = roleFromMe(response.body);

      if (role === null) {
        settle("forbidden", null);
        return;
      }

      if (route.kind === "consent") {
        settle("ready", role);
        return;
      }

      if (!canAccessRouteByRole(route, role)) {
        settle("forbidden", role);
        return;
      }

      if (!requiresConsentCheck(route)) {
        settle("ready", role);
        return;
      }

      apiGet("/consent/status", { headers }).then((consentResponse) => {
        if (!active) return;

        if (!consentResponse.ok) {
          if (consentResponse.status === 401) {
            settle("unauth", null);
            return;
          }
          if (consentResponse.status === 403 && isConsentRequiredBody(consentResponse.body)) {
            settle("consent_required", role);
            return;
          }
          settle("forbidden", role);
          return;
        }

        if (!isRecord(consentResponse.body) || consentResponse.body.is_complete !== true) {
          settle("consent_required", role);
          return;
        }

        settle("ready", role);
      });
    });

    return () => {
      active = false;
    };
  }, [currentRouteKey, guarded, route]);

  useEffect(() => {
    if (!guarded) return;
    if (resolvedRouteKey !== currentRouteKey) return;

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
  }, [currentRouteKey, gateState, guarded, resolvedRouteKey, route]);

  const pending = guarded && resolvedRouteKey !== currentRouteKey;

  return {
    actorRole: pending ? null : actorRole,
    gateState: pending ? "loading" : gateState,
  };
}
