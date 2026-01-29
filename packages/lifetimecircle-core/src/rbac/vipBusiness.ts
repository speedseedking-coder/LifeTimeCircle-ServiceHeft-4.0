import { BadRequestError, ForbiddenError } from "../errors.js";
import type { Subject } from "./roles.js";

export interface VipBusinessStaffChange {
  currentStaffCount: number;
  addStaffCount: number;
  maxStaffAllowed: number; // default 2
}

/**
 * VIP-Gewerbe: max 2 Staff, Freigabe nur SUPERADMIN.
 * -> Diese Funktion prüft nur die Regel und wirft Errors.
 */
export function assertVipBusinessStaffApproval(subject: Subject, change: VipBusinessStaffChange): void {
  if (subject.role !== "admin" || subject.isSuperAdmin !== true) {
    throw new ForbiddenError("VIP-Gewerbe Mitarbeiterplätze dürfen nur durch SUPERADMIN freigegeben werden.");
  }

  const max = change.maxStaffAllowed;
  if (max <= 0) {
    throw new BadRequestError("maxStaffAllowed muss > 0 sein.");
  }

  if (change.currentStaffCount < 0 || change.addStaffCount <= 0) {
    throw new BadRequestError("Ungültige Staff-Änderung.");
  }

  const next = change.currentStaffCount + change.addStaffCount;
  if (next > max) {
    throw new BadRequestError(`Staff-Limit überschritten (max ${max}).`);
  }
}
