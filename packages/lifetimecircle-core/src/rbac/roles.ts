export const ROLES = ["public", "user", "vip", "dealer", "moderator", "admin"] as const;
export type Role = typeof ROLES[number];

export interface Subject {
  userId: string | null; // public => null
  role: Role;
  /**
   * Händler/Gewerbe-Account (Organisation). Optional.
   * - dealer: orgId sollte gesetzt sein
   * - vip (gewerblich): optional, falls ihr VIP-Gewerbe als org-basiert abbildet
   */
  orgId?: string;
  /**
   * Hochrisiko-Operationen (Full-Export, Governance-Freigaben) nur SUPERADMIN.
   * Implementiert als Claim, nicht als eigene Rolle.
   */
  isSuperAdmin?: boolean;
}
