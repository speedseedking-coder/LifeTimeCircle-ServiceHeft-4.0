import { ForbiddenError, UnauthorizedError } from "../errors.js";
import type { Permission } from "./permissions.js";
import type { Subject } from "./roles.js";

export type ResourceType =
  | "vehicle"
  | "entry"
  | "document"
  | "blogPost"
  | "auditRecord"
  | "publicQr";

export interface AccessControlledResource {
  type: ResourceType;
  id: string;

  ownerUserId?: string; // z.B. Fahrzeughalter im System (nicht zwingend realer Halter)
  orgId?: string; // Organisationseigentum (z.B. dealer)
  grantedUserIds?: string[]; // explizite Freigaben (berechtigt)
  grantedOrgIds?: string[]; // Freigabe an Organisation
  isDeleted?: boolean; // soft delete
  vipOnlyImage?: boolean; // VIP-only Bildansicht
}

export interface AuthorizationInput {
  subject: Subject;
  permission: Permission;
  resource?: AccessControlledResource;
}

function isAuthenticated(subject: Subject): boolean {
  return subject.userId !== null && subject.userId !== undefined;
}

function isSuperAdmin(subject: Subject): boolean {
  return subject.role === "admin" && subject.isSuperAdmin === true;
}

function isOwner(subject: Subject, resource: AccessControlledResource): boolean {
  if (!isAuthenticated(subject)) return false;
  return resource.ownerUserId === subject.userId;
}

function isGranted(subject: Subject, resource: AccessControlledResource): boolean {
  if (!isAuthenticated(subject)) return false;

  if (isOwner(subject, resource)) return true;

  if (resource.grantedUserIds?.includes(subject.userId!)) return true;

  if (subject.orgId && resource.grantedOrgIds?.includes(subject.orgId)) return true;

  // dealer: orgId match kann als "implizit berechtigt" gelten, falls Ressourcen org-gebunden sind
  if (subject.role === "dealer" && subject.orgId && resource.orgId === subject.orgId) return true;

  return false;
}

/**
 * Deny-by-default. Unbekannte Permission => false.
 * Serverseitig auf jedem Request nutzen (Controller/Handler).
 */
export function can({ subject, permission, resource }: AuthorizationInput): boolean {
  // Public-QR ist offen (aber nur der Mini-Check, keine Halterdaten)
  if (permission === "publicQr.open" || permission === "publicQr.viewIndicators") {
    return true;
  }

  // Blog lesen ist für alle Rollen erlaubt (auch public)
  if (permission === "blog.read") {
    return true;
  }

  // Moderator: ausschließlich Blog/News (plus blog.read bereits oben)
  if (subject.role === "moderator") {
    if (permission === "blog.write") return isAuthenticated(subject);
    if (permission === "blog.delete.own") return isAuthenticated(subject);
    return false;
  }

  // Nicht-public Operationen: Auth erforderlich
  if (!isAuthenticated(subject)) return false;

  // Admin: technisch alles (RBAC) — Hochrisiko separat über isSuperAdmin
  if (subject.role === "admin") {
    if (permission === "export.full") return isSuperAdmin(subject);
    return true;
  }

  // Dealer / VIP / User – differenziert
  switch (permission) {
    // Fahrzeuge
    case "vehicle.create":
      return subject.role === "user" || subject.role === "vip" || subject.role === "dealer";

    case "vehicle.read.own":
      return resource ? isOwner(subject, resource) : false;

    case "vehicle.read.granted":
      return resource ? isGranted(subject, resource) : false;

    case "vehicle.read.any":
      // niemals für user/vip/dealer ohne explizite Berechtigung; admin handled oben
      return false;

    // Einträge (nur eigene Fahrzeuge / own-scope)
    case "entry.create.own":
    case "entry.update.own":
    case "entry.delete.own":
      return resource ? isOwner(subject, resource) : false;

    // Dokumente
    case "document.upload.own":
      return resource ? isOwner(subject, resource) : false;

    case "document.meta.read.own":
    case "document.content.read.own":
      return resource ? isOwner(subject, resource) : false;

    case "document.meta.read.granted":
    case "document.content.read.granted":
      if (!resource) return false;
      return isGranted(subject, resource);

    case "document.content.read.any":
      // nur VIP/Dealer können "any", aber weiterhin nur wenn berechtigt (granted) — niemals global any
      if (!resource) return false;
      return (subject.role === "vip" || subject.role === "dealer") && isGranted(subject, resource);

    case "image.vipOnly.view":
      if (!resource) return false;
      if (resource.vipOnlyImage !== true) return true;
      return subject.role === "vip" || subject.role === "dealer";

    // Verkauf/Übergabe & interner Verkauf
    case "transfer.generate":
    case "sale.internal.start":
      return subject.role === "vip" || subject.role === "dealer";

    // Audit
    case "audit.read.own":
      return resource ? isOwner(subject, resource) : false;

    case "audit.read.any":
      return false;

    // Newsletter
    case "newsletter.subscription.manage.own":
      return true;

    case "newsletter.send":
      return false;

    // Admin/Governance — nur admin (oben) erlaubt
    case "admin.roles.assign":
    case "admin.moderator.accredit":
    case "admin.vipBusiness.staff.approve":
    case "admin.holderData.read":
      return false;

    // Exports
    case "export.redacted":
      return subject.role === "vip" || subject.role === "dealer" || subject.role === "user";

    case "export.full":
      // nur admin + superadmin claim (oben)
      return false;

    default:
      return false;
  }
}

export function assertCan(input: AuthorizationInput): void {
  const { subject } = input;

  if (!can(input)) {
    if (subject.userId === null) {
      throw new UnauthorizedError("Nicht angemeldet oder ungültiger Public-Zugriff.");
    }
    throw new ForbiddenError("Keine Berechtigung für diese Aktion.");
  }
}
