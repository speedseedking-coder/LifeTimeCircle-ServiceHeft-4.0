import { isRecord } from "../api";
import { isConsentRequired } from "../lib.auth";
import { type Route } from "./appRouting";

export type AppGateState = "loading" | "unauth" | "consent_required" | "ready" | "forbidden";
export type Role = "superadmin" | "admin" | "dealer" | "vip" | "user" | "moderator";
export type NonModeratorRole = Exclude<Role, "moderator">;
type TrustFolderRole = Extract<Role, "superadmin" | "admin" | "dealer" | "vip">;

export const PROTECTED_KINDS: ReadonlySet<Route["kind"]> = new Set([
  "vehicles",
  "vehicleDetail",
  "documents",
  "onboarding",
  "admin",
  "trustFolders",
  "trustFolderDetail",
]);

const TRUST_FOLDER_ROLES: ReadonlySet<TrustFolderRole> = new Set(["superadmin", "admin", "dealer", "vip"]);

export const ROLE_NAV: Record<NonModeratorRole, Array<{ href: string; label: string }>> = {
  superadmin: [
    { href: "#/vehicles", label: "Vehicles" },
    { href: "#/documents", label: "Documents" },
    { href: "#/trust-folders", label: "Trust Folders" },
    { href: "#/onboarding", label: "Onboarding" },
    { href: "#/admin", label: "Admin" },
  ],
  admin: [
    { href: "#/vehicles", label: "Vehicles" },
    { href: "#/documents", label: "Documents" },
    { href: "#/trust-folders", label: "Trust Folders" },
    { href: "#/onboarding", label: "Onboarding" },
    { href: "#/admin", label: "Admin" },
  ],
  dealer: [
    { href: "#/vehicles", label: "Vehicles" },
    { href: "#/documents", label: "Documents" },
    { href: "#/trust-folders", label: "Trust Folders" },
    { href: "#/onboarding", label: "Onboarding" },
  ],
  vip: [
    { href: "#/vehicles", label: "Vehicles" },
    { href: "#/documents", label: "Documents" },
    { href: "#/trust-folders", label: "Trust Folders" },
    { href: "#/onboarding", label: "Onboarding" },
  ],
  user: [
    { href: "#/vehicles", label: "Vehicles" },
    { href: "#/documents", label: "Documents" },
    { href: "#/onboarding", label: "Onboarding" },
  ],
};

export function isGuardedRoute(route: Route): boolean {
  return route.kind === "consent" || PROTECTED_KINDS.has(route.kind);
}

export function roleFromMe(body: unknown): Role | null {
  if (!isRecord(body) || typeof body.role !== "string") return null;
  const role = body.role.toLowerCase();
  if (role === "superadmin" || role === "admin" || role === "dealer" || role === "vip" || role === "user" || role === "moderator") {
    return role;
  }
  return null;
}

export function isConsentRequiredBody(body: unknown): boolean {
  if (isConsentRequired(body)) return true;
  if (isRecord(body)) return isConsentRequired((body as any).detail);
  return false;
}

export function canAccessRouteByRole(route: Route, role: Role | null): boolean {
  if (PROTECTED_KINDS.has(route.kind)) {
    if (role === null || role === "moderator") return false;
    if (route.kind === "admin") {
      return role === "admin" || role === "superadmin";
    }
    if (route.kind === "trustFolders" || route.kind === "trustFolderDetail") {
      return TRUST_FOLDER_ROLES.has(role as TrustFolderRole);
    }
    return true;
  }
  return true;
}

export function safeNextHash(raw: string): string {
  if (!raw.startsWith("#/")) return "#/";
  if (raw.startsWith("#//")) return "#/";
  return raw;
}
