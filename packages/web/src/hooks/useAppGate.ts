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

<<<<<<< HEAD
function routeGateKey(route: Route): string {
  return JSON.stringify(route);
}

export function useAppGate(route: Route): { actorRole: Role | null; gateState: AppGateState } {
  const guarded = isGuardedRoute(route);
  const currentRouteKey = routeGateKey(route);
  const [gateState, setGateState] = useState<AppGateState>(() => (guarded ? "loading" : "ready"));
  const [actorRole, setActorRole] = useState<Role | null>(null);
  const [resolvedRouteKey, setResolvedRouteKey] = useState<string>(() => (guarded ? "" : currentRouteKey));
=======
export function useAppGate(route: Route): { actorRole: Role | null; gateState: AppGateState } {
  const [gateState, setGateState] = useState<AppGateState>(() => (isGuardedRoute(route) ? "loading" : "ready"));
  const [actorRole, setActorRole] = useState<Role | null>(null);
>>>>>>> origin/main

  useEffect(() => {
    let active = true;

<<<<<<< HEAD
    const settle = (nextGateState: AppGateState, nextActorRole: Role | null) => {
      if (!active) return;
      setActorRole(nextActorRole);
      setGateState(nextGateState);
      setResolvedRouteKey(currentRouteKey);
    };

    if (!guarded) {
      setGateState("ready");
      setResolvedRouteKey(currentRouteKey);
=======
    if (!isGuardedRoute(route)) {
      setGateState("ready");
>>>>>>> origin/main
      return () => {
        active = false;
      };
    }

    const token = getAuthToken();
    if (!token) {
<<<<<<< HEAD
      settle("unauth", null);
=======
      setActorRole(null);
      setGateState("unauth");
>>>>>>> origin/main
      return () => {
        active = false;
      };
    }

<<<<<<< HEAD
    setResolvedRouteKey("");
=======
>>>>>>> origin/main
    setGateState("loading");
    const headers = authHeaders(token);

    apiGet("/auth/me", { headers }).then((response) => {
      if (!active) return;

      if (!response.ok) {
        if (response.status === 401) {
<<<<<<< HEAD
          settle("unauth", null);
          return;
        }
        if (response.status === 403 && isConsentRequiredBody(response.body)) {
          settle("consent_required", null);
          return;
        }
        settle("forbidden", null);
=======
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
>>>>>>> origin/main
        return;
      }

      const role = roleFromMe(response.body);
<<<<<<< HEAD

      if (role === null) {
        settle("forbidden", null);
=======
      setActorRole(role);

      if (role === null) {
        setGateState("forbidden");
>>>>>>> origin/main
        return;
      }

      if (route.kind === "consent") {
<<<<<<< HEAD
        settle("ready", role);
=======
        setGateState("ready");
>>>>>>> origin/main
        return;
      }

      if (!canAccessRouteByRole(route, role)) {
<<<<<<< HEAD
        settle("forbidden", role);
=======
        setGateState("forbidden");
>>>>>>> origin/main
        return;
      }

      apiGet("/consent/status", { headers }).then((consentResponse) => {
        if (!active) return;

        if (!consentResponse.ok) {
          if (consentResponse.status === 401) {
<<<<<<< HEAD
            settle("unauth", null);
            return;
          }
          if (consentResponse.status === 403 && isConsentRequiredBody(consentResponse.body)) {
            settle("consent_required", role);
            return;
          }
          settle("forbidden", role);
=======
            setGateState("unauth");
            return;
          }
          if (consentResponse.status === 403 && isConsentRequiredBody(consentResponse.body)) {
            setGateState("consent_required");
            return;
          }
          setGateState("forbidden");
>>>>>>> origin/main
          return;
        }

        if (!isRecord(consentResponse.body) || consentResponse.body.is_complete !== true) {
<<<<<<< HEAD
          settle("consent_required", role);
          return;
        }

        settle("ready", role);
=======
          setGateState("consent_required");
          return;
        }

        setGateState("ready");
>>>>>>> origin/main
      });
    });

    return () => {
      active = false;
    };
<<<<<<< HEAD
  }, [currentRouteKey, guarded, route]);

  useEffect(() => {
    if (!guarded) return;
    if (resolvedRouteKey !== currentRouteKey) return;
=======
  }, [route]);

  useEffect(() => {
    if (!isGuardedRoute(route)) return;
>>>>>>> origin/main

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
<<<<<<< HEAD
  }, [currentRouteKey, gateState, guarded, resolvedRouteKey, route]);

  const pending = guarded && resolvedRouteKey !== currentRouteKey;

  return {
    actorRole: pending ? null : actorRole,
    gateState: pending ? "loading" : gateState,
  };
=======
  }, [gateState, route]);

  return { actorRole, gateState };
>>>>>>> origin/main
}
