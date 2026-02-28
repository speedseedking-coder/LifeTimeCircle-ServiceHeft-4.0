import { apiGet, apiPost, extractApiError, isRecord, type ApiResult } from "./api";

export type AdminApiResult<T> =
  | { ok: true; status: number; body: T }
  | { ok: false; status: number; body?: unknown; error: string };

export type AdminUser = {
  user_id: string;
  role: string;
  created_at: string;
};

export type RoleChangeResponse = {
  ok: boolean;
  user_id: string;
  old_role: string;
  new_role: string;
  at: string;
};

export type VipBusiness = {
  business_id: string;
  owner_user_id: string;
  approved: boolean;
  created_at: string;
  approved_at: string | null;
  approved_by_user_id: string | null;
  staff_user_ids: string[];
  staff_count: number;
};

export type VipBusinessCreatePayload = {
  owner_user_id: string;
  business_id?: string | null;
  reason?: string | null;
};

export type ExportTargetKind = "vehicle" | "user" | "servicebook";

export type ExportGrant = {
  export_token: string;
  token: string;
  expires_at: string;
  ttl_seconds: number;
  one_time: boolean;
  header: string;
};

export type FullExportCiphertext = {
  ciphertext: string;
  alg: string;
  one_time: boolean;
};

function normalizeResult<T>(res: ApiResult, map: (body: unknown) => T | null): AdminApiResult<T> {
  if (!res.ok) return { ok: false, status: res.status, body: res.body, error: extractApiError(res.body) ?? res.error };
  const mapped = map(res.body);
  if (mapped === null) return { ok: false, status: 500, body: res.body, error: "invalid_body" };
  return { ok: true, status: res.status, body: mapped };
}

function mapAdminUser(body: unknown): AdminUser | null {
  if (!isRecord(body)) return null;
  if (typeof body.user_id !== "string" || typeof body.role !== "string" || typeof body.created_at !== "string") return null;
  return { user_id: body.user_id, role: body.role, created_at: body.created_at };
}

function mapRoleChangeResponse(body: unknown): RoleChangeResponse | null {
  if (!isRecord(body)) return null;
  if (
    typeof body.ok !== "boolean" ||
    typeof body.user_id !== "string" ||
    typeof body.old_role !== "string" ||
    typeof body.new_role !== "string" ||
    typeof body.at !== "string"
  ) {
    return null;
  }
  return {
    ok: body.ok,
    user_id: body.user_id,
    old_role: body.old_role,
    new_role: body.new_role,
    at: body.at,
  };
}

function mapVipBusiness(body: unknown): VipBusiness | null {
  if (!isRecord(body)) return null;
  if (
    typeof body.business_id !== "string" ||
    typeof body.owner_user_id !== "string" ||
    typeof body.approved !== "boolean" ||
    typeof body.created_at !== "string"
  ) {
    return null;
  }

  const staff_user_ids = Array.isArray(body.staff_user_ids) ? body.staff_user_ids.filter((item): item is string => typeof item === "string") : [];

  return {
    business_id: body.business_id,
    owner_user_id: body.owner_user_id,
    approved: body.approved,
    created_at: body.created_at,
    approved_at: typeof body.approved_at === "string" ? body.approved_at : null,
    approved_by_user_id: typeof body.approved_by_user_id === "string" ? body.approved_by_user_id : null,
    staff_user_ids,
    staff_count: typeof body.staff_count === "number" ? body.staff_count : staff_user_ids.length,
  };
}

function mapExportGrant(body: unknown): ExportGrant | null {
  if (!isRecord(body)) return null;
  if (
    typeof body.export_token !== "string" ||
    typeof body.token !== "string" ||
    typeof body.expires_at !== "string" ||
    typeof body.ttl_seconds !== "number" ||
    typeof body.one_time !== "boolean" ||
    typeof body.header !== "string"
  ) {
    return null;
  }
  return {
    export_token: body.export_token,
    token: body.token,
    expires_at: body.expires_at,
    ttl_seconds: body.ttl_seconds,
    one_time: body.one_time,
    header: body.header,
  };
}

function mapFullExportCiphertext(body: unknown): FullExportCiphertext | null {
  if (!isRecord(body)) return null;
  if (typeof body.ciphertext !== "string" || typeof body.alg !== "string" || typeof body.one_time !== "boolean") return null;
  return {
    ciphertext: body.ciphertext,
    alg: body.alg,
    one_time: body.one_time,
  };
}

function mapAdminUserList(body: unknown): AdminUser[] | null {
  if (!Array.isArray(body)) return null;
  const mapped = body.map(mapAdminUser).filter((item): item is AdminUser => item !== null);
  return mapped;
}

function mapVipBusinessList(body: unknown): VipBusiness[] | null {
  if (!Array.isArray(body)) return null;
  const mapped = body.map(mapVipBusiness).filter((item): item is VipBusiness => item !== null);
  return mapped;
}

function exportPath(kind: ExportTargetKind, targetId: string): string {
  return `/export/${kind}/${encodeURIComponent(targetId)}`;
}

export async function listAdminUsers(init?: RequestInit): Promise<AdminApiResult<AdminUser[]>> {
  const res = await apiGet("/admin/users", init);
  return normalizeResult(res, mapAdminUserList);
}

export async function setAdminUserRole(userId: string, role: string, reason: string, init?: RequestInit): Promise<AdminApiResult<RoleChangeResponse>> {
  const res = await apiPost(`/admin/users/${encodeURIComponent(userId)}/role`, { role, reason }, init);
  return normalizeResult(res, mapRoleChangeResponse);
}

export async function accreditModerator(userId: string, reason: string, init?: RequestInit): Promise<AdminApiResult<RoleChangeResponse>> {
  const res = await apiPost(`/admin/users/${encodeURIComponent(userId)}/moderator`, { reason }, init);
  return normalizeResult(res, mapRoleChangeResponse);
}

export async function listVipBusinesses(init?: RequestInit): Promise<AdminApiResult<VipBusiness[]>> {
  const res = await apiGet("/admin/vip-businesses", init);
  return normalizeResult(res, mapVipBusinessList);
}

export async function createVipBusiness(payload: VipBusinessCreatePayload, init?: RequestInit): Promise<AdminApiResult<VipBusiness>> {
  const res = await apiPost("/admin/vip-businesses", payload, init);
  return normalizeResult(res, (body) => {
    const mapped = mapVipBusiness(body);
    if (!mapped) {
      const fallback = mapVipBusiness({ ...(isRecord(body) ? body : {}), staff_user_ids: [], staff_count: 0 });
      return fallback;
    }
    return mapped;
  });
}

export async function approveVipBusiness(businessId: string, init?: RequestInit): Promise<AdminApiResult<VipBusiness>> {
  const res = await apiPost(`/admin/vip-businesses/${encodeURIComponent(businessId)}/approve`, undefined, init);
  return normalizeResult(res, (body) => {
    const mapped = mapVipBusiness(body);
    if (!mapped) {
      const fallback = mapVipBusiness({ ...(isRecord(body) ? body : {}), staff_user_ids: [], staff_count: 0 });
      return fallback;
    }
    return mapped;
  });
}

export async function addVipBusinessStaff(
  businessId: string,
  userId: string,
  reason: string,
  init?: RequestInit,
): Promise<AdminApiResult<{ ok: boolean; business_id: string; user_id: string; at: string }>> {
  const res = await apiPost(`/admin/vip-businesses/${encodeURIComponent(businessId)}/staff/${encodeURIComponent(userId)}`, { reason }, init);
  return normalizeResult(res, (body) => {
    if (!isRecord(body)) return null;
    if (
      typeof body.ok !== "boolean" ||
      typeof body.business_id !== "string" ||
      typeof body.user_id !== "string" ||
      typeof body.at !== "string"
    ) {
      return null;
    }
    return {
      ok: body.ok,
      business_id: body.business_id,
      user_id: body.user_id,
      at: body.at,
    };
  });
}

export async function fetchRedactedExport(kind: ExportTargetKind, targetId: string, init?: RequestInit): Promise<AdminApiResult<unknown>> {
  const res = await apiGet(exportPath(kind, targetId), init);
  if (!res.ok) return { ok: false, status: res.status, body: res.body, error: extractApiError(res.body) ?? res.error };
  return { ok: true, status: res.status, body: res.body };
}

export async function requestFullExportGrant(
  kind: ExportTargetKind,
  targetId: string,
  ttlSeconds: number,
  init?: RequestInit,
): Promise<AdminApiResult<ExportGrant>> {
  const res = await apiPost(`${exportPath(kind, targetId)}/grant?ttl_seconds=${encodeURIComponent(String(ttlSeconds))}`, undefined, init);
  return normalizeResult(res, mapExportGrant);
}

export async function fetchFullExportCiphertext(
  kind: ExportTargetKind,
  targetId: string,
  exportToken: string,
  init?: RequestInit,
): Promise<AdminApiResult<FullExportCiphertext>> {
  const res = await apiGet(`${exportPath(kind, targetId)}/full`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      "X-Export-Token": exportToken,
    },
  });
  return normalizeResult(res, mapFullExportCiphertext);
}
