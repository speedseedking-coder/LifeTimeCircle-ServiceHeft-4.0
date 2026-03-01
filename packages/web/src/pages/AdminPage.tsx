import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { prettyBody } from "../api";
import InlineErrorBanner from "../components/InlineErrorBanner";
import {
  accreditModerator,
  addVipBusinessStaff,
  approveVipBusiness,
  createVipBusiness,
  fetchFullExportCiphertext,
  fetchRedactedExport,
  listAdminUsers,
  listVipBusinesses,
  requestAdminStepUpGrant,
  requestFullExportGrant,
  setAdminUserRole,
  type AdminApiResult,
  type AdminStepUpScope,
  type AdminUser,
  type ExportGrant,
  type ExportTargetKind,
  type FullExportCiphertext,
  type VipBusiness,
} from "../adminApi";
import { authHeaders, getAuthToken } from "../lib.auth";
import { handleUnauthorized } from "../lib/handleUnauthorized";

type AdminActorRole = "admin" | "superadmin";

const ROLE_OPTIONS = ["public", "user", "vip", "dealer", "moderator", "admin", "superadmin"] as const;
const ADMIN_STEP_UP_TTL_SECONDS = 600;

function sortUsers(rows: AdminUser[]): AdminUser[] {
  return [...rows].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
}

function sortBusinesses(rows: VipBusiness[]): VipBusiness[] {
  return [...rows].sort((a, b) => {
    if (a.approved !== b.approved) return a.approved ? 1 : -1;
    return a.created_at < b.created_at ? 1 : -1;
  });
}

function headers(extraHeaders?: Record<string, string>): { headers: Record<string, string> } {
  return { headers: { ...authHeaders(getAuthToken()), ...(extraHeaders ?? {}) } };
}

function extractErrorMessage(result: { status: number; error: string }): string {
  if (result.status === 0) return "Netzwerkfehler beim Laden der Admin-Daten.";
  if (result.status === 401) return "Session abgelaufen. Bitte erneut anmelden.";
  if (result.status === 403 && result.error === "admin_step_up_required") return "Für diese Admin-Aktion ist ein Step-up erforderlich.";
  if (result.status === 403 && result.error === "admin_step_up_invalid") return "Der Step-up ist ungültig oder abgelaufen. Bitte Aktion erneut auslösen.";
  if (result.status === 403 && result.error === "superadmin_required") return "Diese Aktion ist nur für SUPERADMIN erlaubt.";
  if (result.status === 403 && result.error === "export_grant_rejected") return "Der Voll-Export wurde vom Server abgelehnt. Prüfe Grant, Ziel-ID und Ablaufzeit.";
  if (result.status === 403 && result.error === "forbidden") return "Kein Zugriff auf diese Admin-Aktion.";
  if (result.status === 404 && result.error === "user_not_found") return "User-ID wurde nicht gefunden.";
  if (result.status === 404 && result.error === "business_not_found") return "Business-ID wurde nicht gefunden.";
  if (result.status === 404 && result.error === "not_found") return "Zieldatensatz wurde nicht gefunden.";
  if (result.status === 409 && result.error === "staff_limit_reached") return "Für dieses VIP-Business sind keine weiteren Staff-Slots frei.";
  if (result.status === 400 && result.error === "business_not_approved") return "Staff kann erst nach SUPERADMIN-Freigabe hinzugefügt werden.";
  if (result.status === 400 && result.error === "invalid_role") return "Die Zielrolle ist ungültig.";
  if (result.status === 400 && result.error === "missing_export_token") return "Für den Voll-Export fehlt ein gültiger Export-Grant.";
  if (
    result.status === 403 &&
    (result.error === "invalid_export_token" ||
      result.error === "expired_export_token" ||
      result.error === "export_token_invalid" ||
      result.error === "export_token_expired" ||
      result.error === "export_token_already_used")
  ) {
    return "Der Export-Grant ist ungültig, abgelaufen oder bereits verbraucht. Bitte neuen Grant anfordern.";
  }
  if (result.status === 500 && result.error === "invalid_body") return "Serverantwort hatte ein unerwartetes Format. Bitte Backend prüfen.";
  return "Die Admin-Aktion konnte nicht ausgeführt werden.";
}

function AdminUserCard(props: {
  actorRole: AdminActorRole;
  user: AdminUser;
  currentRole: string;
  currentReason: string;
  busy: boolean;
  onRoleChange: (role: string) => void;
  onReasonChange: (reason: string) => void;
  onSaveRole: () => void;
  onAccreditModerator: () => void;
}): JSX.Element {
  const superadminOptionLocked = props.actorRole !== "superadmin";
  const roleChanged = props.currentRole !== props.user.role;

  return (
    <article className="ltc-card ltc-section ltc-section--card">
      <div className="ltc-admin-head">
        <div>
          <div className="ltc-card__title">
            <code>{props.user.user_id}</code>
          </div>
          <div className="ltc-muted">
            Aktuelle Rolle: <strong>{props.user.role}</strong> · erstellt {new Date(props.user.created_at).toLocaleString("de-DE")}
          </div>
        </div>
      </div>

      <div className="ltc-admin-form ltc-admin-form--narrow">
        <label>
          Zielrolle
          <select
            id={`admin-role-${props.user.user_id}`}
            value={props.currentRole}
            onChange={(e) => props.onRoleChange(e.target.value)}
            className="ltc-form-group__select"
            aria-required="true"
          >
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role} disabled={role === "superadmin" && superadminOptionLocked}>
                {role}
              </option>
            ))}
          </select>
        </label>

        <label>
          Grund (optional)
          <input
            id={`admin-reason-${props.user.user_id}`}
            value={props.currentReason}
            onChange={(e) => props.onReasonChange(e.target.value)}
            placeholder="Wird nur als reason_provided auditiert"
            autoComplete="off"
            className="ltc-form-group__input"
          />
        </label>
      </div>

      <div className="ltc-admin-actions">
        <button type="button" className="ltc-btn ltc-btn--primary" disabled={props.busy || !roleChanged} onClick={props.onSaveRole}>
          Rolle setzen
        </button>
        <button type="button" className="ltc-btn ltc-btn--ghost" disabled={props.busy || props.user.role === "moderator"} onClick={props.onAccreditModerator}>
          Als Moderator akkreditieren
        </button>
      </div>
    </article>
  );
}

function VipBusinessCard(props: {
  actorRole: AdminActorRole;
  business: VipBusiness;
  staffDraft: string;
  staffReason: string;
  busy: boolean;
  onStaffDraftChange: (value: string) => void;
  onStaffReasonChange: (value: string) => void;
  onApprove: () => void;
  onAddStaff: () => void;
}): JSX.Element {
  const staffInvalid = props.staffDraft.trim().length > 0 && props.staffDraft.trim().length < 8;

  return (
    <article className="ltc-card ltc-section ltc-section--card">
      <div className="ltc-admin-head">
        <div>
          <div className="ltc-card__title">
            <code>{props.business.business_id}</code>
          </div>
          <div className="ltc-muted">
            Owner: <code>{props.business.owner_user_id}</code> · Status: <strong>{props.business.approved ? "approved" : "pending"}</strong>
          </div>
          <div className="ltc-meta">
            erstellt {new Date(props.business.created_at).toLocaleString("de-DE")}
            {props.business.approved_at ? ` · freigegeben ${new Date(props.business.approved_at).toLocaleString("de-DE")}` : ""}
            {props.business.approved_by_user_id ? ` · durch ${props.business.approved_by_user_id}` : ""}
          </div>
        </div>

        {props.actorRole === "superadmin" && !props.business.approved ? (
          <button type="button" className="ltc-btn ltc-btn--primary" disabled={props.busy} onClick={props.onApprove}>
            Freigeben
          </button>
        ) : null}
      </div>

      <div className="ltc-muted ltc-mt-2">
        Staff ({props.business.staff_count}/2):{" "}
        {props.business.staff_user_ids.length > 0 ? props.business.staff_user_ids.map((id) => <code key={id}>{id} </code>) : "noch keiner"}
      </div>

      {props.actorRole === "superadmin" ? (
        <div className="ltc-admin-form ltc-admin-form--narrow">
          <label>
            Staff User-ID
            <input
              id={`admin-staff-${props.business.business_id}`}
              value={props.staffDraft}
              onChange={(e) => props.onStaffDraftChange(e.target.value)}
              placeholder="bestehende auth_users user_id"
              autoComplete="off"
              className="ltc-form-group__input"
              aria-required="true"
              aria-invalid={staffInvalid}
              aria-describedby={staffInvalid ? `admin-staff-error-${props.business.business_id}` : undefined}
            />
          </label>
          {staffInvalid ? (
            <p id={`admin-staff-error-${props.business.business_id}`} className="ltc-helper-text ltc-helper-text--error">
              Staff User-ID muss mindestens 8 Zeichen lang sein.
            </p>
          ) : null}

          <label>
            Grund (optional)
            <input
              value={props.staffReason}
              onChange={(e) => props.onStaffReasonChange(e.target.value)}
              placeholder="Wird nur als reason_provided auditiert"
              autoComplete="off"
              className="ltc-form-group__input"
            />
          </label>

          <div className="ltc-admin-actions">
            <button type="button" className="ltc-btn ltc-btn--ghost" disabled={props.busy || props.staffDraft.trim().length < 8} onClick={props.onAddStaff}>
              Staff hinzufügen
            </button>
          </div>
        </div>
      ) : null}
    </article>
  );
}

export default function AdminPage(props: { actorRole: AdminActorRole }): JSX.Element {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [vipBusinesses, setVipBusinesses] = useState<VipBusiness[]>([]);
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState<"businessOwner" | "exportTarget" | "exportTtl" | null>(null);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState("");
  const [roleDrafts, setRoleDrafts] = useState<Record<string, string>>({});
  const [reasonDrafts, setReasonDrafts] = useState<Record<string, string>>({});
  const [staffDrafts, setStaffDrafts] = useState<Record<string, string>>({});
  const [staffReasonDrafts, setStaffReasonDrafts] = useState<Record<string, string>>({});
  const [businessOwnerUserId, setBusinessOwnerUserId] = useState("");
  const [businessId, setBusinessId] = useState("");
  const [businessReason, setBusinessReason] = useState("");
  const [exportKind, setExportKind] = useState<ExportTargetKind>("vehicle");
  const [exportTargetId, setExportTargetId] = useState("");
  const [exportTtlSeconds, setExportTtlSeconds] = useState("300");
  const [exportGrant, setExportGrant] = useState<ExportGrant | null>(null);
  const [redactedExportBody, setRedactedExportBody] = useState<unknown>(null);
  const [fullExportBody, setFullExportBody] = useState<FullExportCiphertext | null>(null);
  const businessOwnerRef = useRef<HTMLInputElement | null>(null);
  const exportTargetRef = useRef<HTMLInputElement | null>(null);
  const exportTtlRef = useRef<HTMLInputElement | null>(null);

  const isSuperadmin = props.actorRole === "superadmin";
  const visibleUsers = useMemo(() => sortUsers(users), [users]);
  const visibleBusinesses = useMemo(() => sortBusinesses(vipBusinesses), [vipBusinesses]);
  const ownerUserIdInvalid = businessOwnerUserId.trim().length > 0 && businessOwnerUserId.trim().length < 8;
  const exportTtlInvalid = exportTtlSeconds.trim().length > 0 && !Number.isFinite(Number.parseInt(exportTtlSeconds, 10));

  useEffect(() => {
    setRoleDrafts((prev) => {
      const next = { ...prev };
      for (const user of users) {
        if (!next[user.user_id]) next[user.user_id] = user.role;
      }
      return next;
    });
  }, [users]);

  async function loadAll() {
    setLoading(true);
    setError("");
    setErrorField(null);
    const [usersRes, businessesRes] = await Promise.all([listAdminUsers(headers()), listVipBusinesses(headers())]);
    setLoading(false);

    if (!usersRes.ok) {
      if (usersRes.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(extractErrorMessage(usersRes));
      return;
    }

    if (!businessesRes.ok) {
      if (businessesRes.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(extractErrorMessage(businessesRes));
      return;
    }

    setUsers(usersRes.body);
    setVipBusinesses(businessesRes.body);
  }

  useEffect(() => {
    void loadAll();
  }, []);

  async function runAction<T>(key: string, action: () => Promise<AdminApiResult<T>>, onSuccess: (body: T) => void, successMessage: string) {
    setBusyKey(key);
    setError("");
    setErrorField(null);
    setNotice("");
    const result = await action();
    setBusyKey("");

    if (!result.ok) {
      if (result.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(extractErrorMessage(result));
      return;
    }

    onSuccess(result.body);
    setNotice(successMessage);
  }

  async function runSensitiveAction<T>(
    key: string,
    scope: AdminStepUpScope,
    action: (init: { headers: Record<string, string> }) => Promise<AdminApiResult<T>>,
    onSuccess: (body: T) => void,
    successMessage: string,
  ) {
    setBusyKey(key);
    setError("");
    setErrorField(null);
    setNotice("");

    const grant = await requestAdminStepUpGrant(scope, ADMIN_STEP_UP_TTL_SECONDS, headers());
    if (!grant.ok) {
      setBusyKey("");
      if (grant.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(extractErrorMessage(grant));
      return;
    }

    const result = await action(headers({ [grant.body.header]: grant.body.step_up_token }));
    setBusyKey("");

    if (!result.ok) {
      if (result.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(extractErrorMessage(result));
      return;
    }

    onSuccess(result.body);
    setNotice(successMessage);
  }

  function updateUserRole(userId: string, nextRole: string) {
    setUsers((prev) => prev.map((user) => (user.user_id === userId ? { ...user, role: nextRole } : user)));
    setRoleDrafts((prev) => ({ ...prev, [userId]: nextRole }));
  }

  function upsertVipBusiness(nextBusiness: VipBusiness) {
    setVipBusinesses((prev) => {
      const exists = prev.some((item) => item.business_id === nextBusiness.business_id);
      if (!exists) return [nextBusiness, ...prev];
      return prev.map((item) => (item.business_id === nextBusiness.business_id ? nextBusiness : item));
    });
  }

  return (
    <main className="ltc-main ltc-main--xl" data-testid="admin-page">
      <section className="ltc-page-intro">
        <div className="ltc-page-intro__copy">
          <div className="ltc-page-intro__eyebrow">Operations</div>
          <h1>Admin</h1>
          <p>Rollen, Moderator-Akkreditierung, VIP-Business-Freigaben und Export-Step-up auf den produktiven Server-Contracts.</p>
        </div>
        <div className="ltc-page-intro__meta">
          <div className="ltc-kpi-tile">
            <div className="ltc-kpi-tile__label">Actor</div>
            <div className="ltc-kpi-tile__value">{props.actorRole}</div>
            <div className="ltc-kpi-tile__meta">Aktive Admin-Sicht</div>
          </div>
        </div>
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}
      {notice ? (
        <section className="ltc-card ltc-card--compact ltc-section ltc-state-panel ltc-state-panel--info" role="status" aria-live="polite" data-testid="admin-notice">
          <div className="ltc-state-panel__title">Status</div>
          <p className="ltc-state-panel__copy">{notice}</p>
        </section>
      ) : null}

      {loading ? (
        <section className="ltc-card ltc-section ltc-section--card">
          <div className="ltc-muted">Admin-Daten werden geladen...</div>
        </section>
      ) : null}

      {!loading ? (
        <>
          <div className="ltc-kpi-band">
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Users</div>
              <div className="ltc-kpi-tile__value">{visibleUsers.length}</div>
              <div className="ltc-kpi-tile__meta">Serverseitig sichtbare Accounts</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">VIP-Businesses</div>
              <div className="ltc-kpi-tile__value">{visibleBusinesses.length}</div>
              <div className="ltc-kpi-tile__meta">Anträge und freigegebene Business-Container</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Pending</div>
              <div className="ltc-kpi-tile__value">{visibleBusinesses.filter((item) => !item.approved).length}</div>
              <div className="ltc-kpi-tile__meta">Warten auf SUPERADMIN-Step-up</div>
            </div>
            <div className="ltc-kpi-tile">
              <div className="ltc-kpi-tile__label">Export-Grant</div>
              <div className="ltc-kpi-tile__value">{exportGrant ? "aktiv" : "none"}</div>
              <div className="ltc-kpi-tile__meta">{exportGrant ? "One-time Token vorhanden" : "Noch kein Full-Grant erstellt"}</div>
            </div>
          </div>

          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Access</span>
            <div className="ltc-card__title">Rollen & Moderator</div>
            <div className="ltc-muted">
              Der Server auditiert nur ID-bezogene Metadaten und `reason_provided`, keine Freitext-Begründungen. Sensible Aktionen holen automatisch einen One-time Step-up.
            </div>
            {visibleUsers.length === 0 ? <p className="ltc-muted ltc-mt-4">Keine Nutzer gefunden.</p> : null}
            <div className="ltc-admin-list">
              {visibleUsers.map((user) => (
                <AdminUserCard
                  key={user.user_id}
                  actorRole={props.actorRole}
                  user={user}
                  currentRole={roleDrafts[user.user_id] ?? user.role}
                  currentReason={reasonDrafts[user.user_id] ?? ""}
                  busy={busyKey === `role:${user.user_id}` || busyKey === `moderator:${user.user_id}`}
                  onRoleChange={(role) => setRoleDrafts((prev) => ({ ...prev, [user.user_id]: role }))}
                  onReasonChange={(reason) => setReasonDrafts((prev) => ({ ...prev, [user.user_id]: reason }))}
                  onSaveRole={() =>
                    void runSensitiveAction(
                      `role:${user.user_id}`,
                      "role_grant",
                      (init) => setAdminUserRole(user.user_id, roleDrafts[user.user_id] ?? user.role, reasonDrafts[user.user_id] ?? "", init),
                      (body) => updateUserRole(user.user_id, body.new_role),
                      `Rolle für ${user.user_id} wurde auf ${roleDrafts[user.user_id] ?? user.role} gesetzt.`,
                    )
                  }
                  onAccreditModerator={() =>
                    void runSensitiveAction(
                      `moderator:${user.user_id}`,
                      "moderator_accredit",
                      (init) => accreditModerator(user.user_id, reasonDrafts[user.user_id] ?? "", init),
                      (body) => updateUserRole(user.user_id, body.new_role),
                      `Moderator-Akkreditierung für ${user.user_id} abgeschlossen.`,
                    )
                  }
                />
              ))}
            </div>
          </section>

          <div className="ltc-layout-grid ltc-layout-grid--sidebar ltc-section" data-testid="admin-desktop-grid">
          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Business</span>
            <div className="ltc-card__title">VIP-Businesses</div>
            <div className="ltc-muted">
              Admin kann Requests anlegen. Freigabe und Staff-Zuordnung bleiben serverseitig auf SUPERADMIN begrenzt und erfordern pro Aktion einen frischen Step-up.
            </div>

            <form
              className="ltc-admin-form"
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                const ownerUserId = businessOwnerUserId.trim();
                if (ownerUserId.length < 8) {
                  setError("Owner User-ID ist zu kurz.");
                  setErrorField("businessOwner");
                  setNotice("");
                  businessOwnerRef.current?.focus();
                  return;
                }
                void runAction(
                  "business:create",
                  () =>
                    createVipBusiness(
                      {
                        owner_user_id: ownerUserId,
                        business_id: businessId.trim() || undefined,
                        reason: businessReason.trim() || undefined,
                      },
                      headers(),
                    ),
                  (body) => {
                    upsertVipBusiness(body);
                    setBusinessOwnerUserId("");
                    setBusinessId("");
                    setBusinessReason("");
                    void loadAll();
                  },
                  `VIP-Business ${businessId.trim() || "neu"} wurde angelegt bzw. bestätigt.`,
                );
              }}
            >
              <label>
                Owner User-ID
                <input
                  ref={businessOwnerRef}
                  id="admin-business-owner-id"
                  value={businessOwnerUserId}
                  onChange={(e) => {
                    setBusinessOwnerUserId(e.target.value);
                    if (errorField === "businessOwner") setErrorField(null);
                  }}
                  placeholder="bestehende auth_users user_id"
                  autoComplete="off"
                  className="ltc-form-group__input"
                  aria-required="true"
                  aria-invalid={ownerUserIdInvalid}
                  aria-describedby={ownerUserIdInvalid || errorField === "businessOwner" ? "admin-business-owner-error" : undefined}
                />
              </label>
              {ownerUserIdInvalid || errorField === "businessOwner" ? (
                <p id="admin-business-owner-error" className="ltc-helper-text ltc-helper-text--error">
                  Owner User-ID muss mindestens 8 Zeichen lang sein.
                </p>
              ) : null}

              <label>
                Business-ID (optional)
                <input
                  id="admin-business-id"
                  value={businessId}
                  onChange={(e) => setBusinessId(e.target.value)}
                  placeholder="externes Business-Kürzel oder leer für UUID"
                  autoComplete="off"
                  className="ltc-form-group__input"
                />
              </label>

              <label>
                Grund (optional)
                <input
                  id="admin-business-reason"
                  value={businessReason}
                  onChange={(e) => setBusinessReason(e.target.value)}
                  placeholder="Wird nur als reason_provided auditiert"
                  autoComplete="off"
                  className="ltc-form-group__input"
                />
              </label>

              <div className="ltc-admin-actions">
                <button type="submit" className="ltc-btn ltc-btn--primary" disabled={busyKey === "business:create"}>
                  VIP-Business anlegen
                </button>
              </div>
            </form>

            {visibleBusinesses.length === 0 ? <p className="ltc-muted ltc-mt-4">Noch keine VIP-Businesses vorhanden.</p> : null}
            {visibleBusinesses.map((business) => (
              <VipBusinessCard
                key={business.business_id}
                actorRole={props.actorRole}
                business={business}
                staffDraft={staffDrafts[business.business_id] ?? ""}
                staffReason={staffReasonDrafts[business.business_id] ?? ""}
                busy={busyKey === `business:approve:${business.business_id}` || busyKey === `business:staff:${business.business_id}`}
                onStaffDraftChange={(value) => setStaffDrafts((prev) => ({ ...prev, [business.business_id]: value }))}
                onStaffReasonChange={(value) => setStaffReasonDrafts((prev) => ({ ...prev, [business.business_id]: value }))}
                onApprove={() =>
                  void runSensitiveAction(
                    `business:approve:${business.business_id}`,
                    "vip_business_approve",
                    (init) => approveVipBusiness(business.business_id, init),
                    () => {
                      void loadAll();
                    },
                    `VIP-Business ${business.business_id} wurde freigegeben.`,
                  )
                }
                onAddStaff={() =>
                  void runSensitiveAction(
                    `business:staff:${business.business_id}`,
                    "vip_business_staff",
                    (init) =>
                      addVipBusinessStaff(
                        business.business_id,
                        staffDrafts[business.business_id] ?? "",
                        staffReasonDrafts[business.business_id] ?? "",
                        init,
                      ),
                    () => {
                      setStaffDrafts((prev) => ({ ...prev, [business.business_id]: "" }));
                      setStaffReasonDrafts((prev) => ({ ...prev, [business.business_id]: "" }));
                      void loadAll();
                    },
                    `Staff für ${business.business_id} wurde ergänzt.`,
                  )
                }
              />
            ))}
          </section>

          <div className="ltc-admin-rail">
          <section className="ltc-card ltc-section ltc-section--card">
            <span className="ltc-card__eyebrow">Export</span>
            <div className="ltc-card__title">Export-Step-up</div>
            <div className="ltc-muted">
              Redacted Exports sind für Admin und SUPERADMIN nutzbar. One-time Full Exports mit `X-Export-Token` bleiben strikt SUPERADMIN-only.
            </div>

            <form
              className="ltc-admin-form"
              onSubmit={(e) => e.preventDefault()}
            >
              <label>
                Zieltyp
                <select value={exportKind} onChange={(e) => setExportKind(e.target.value as ExportTargetKind)} className="ltc-form-group__select">
                  <option value="vehicle">vehicle</option>
                  <option value="user">user</option>
                  <option value="servicebook">servicebook</option>
                </select>
              </label>

              <label>
                Ziel-ID
                <input
                  id="admin-export-target-id"
                  ref={exportTargetRef}
                  value={exportTargetId}
                  onChange={(e) => {
                    setExportTargetId(e.target.value);
                    if (errorField === "exportTarget") setErrorField(null);
                  }}
                  placeholder="vehicle_id / user_id / servicebook_id"
                  autoComplete="off"
                  className="ltc-form-group__input"
                  aria-required="true"
                  aria-invalid={errorField === "exportTarget"}
                  aria-describedby={errorField === "exportTarget" ? "admin-export-target-error" : undefined}
                />
              </label>
              {errorField === "exportTarget" ? (
                <p id="admin-export-target-error" className="ltc-helper-text ltc-helper-text--error">
                  Ziel-ID ist erforderlich.
                </p>
              ) : null}

              <label>
                TTL Sekunden (für Full Grant)
                <input
                  id="admin-export-ttl"
                  ref={exportTtlRef}
                  value={exportTtlSeconds}
                  onChange={(e) => {
                    setExportTtlSeconds(e.target.value);
                    if (errorField === "exportTtl") setErrorField(null);
                  }}
                  inputMode="numeric"
                  autoComplete="off"
                  className="ltc-form-group__input"
                  aria-required="true"
                  aria-invalid={exportTtlInvalid}
                  aria-describedby={exportTtlInvalid || errorField === "exportTtl" ? "admin-export-ttl-error" : undefined}
                />
              </label>
              {exportTtlInvalid || errorField === "exportTtl" ? (
                <p id="admin-export-ttl-error" className="ltc-helper-text ltc-helper-text--error">
                  TTL muss numerisch sein.
                </p>
              ) : null}

              <div className="ltc-admin-actions">
                <button
                  type="button"
                  className="ltc-btn ltc-btn--primary"
                  disabled={busyKey === "export:redacted"}
                  onClick={() => {
                    if (exportTargetId.trim().length === 0) {
                      setError("Ziel-ID ist erforderlich.");
                      setErrorField("exportTarget");
                      setNotice("");
                      exportTargetRef.current?.focus();
                      return;
                    }
                    void runAction(
                      "export:redacted",
                      () => fetchRedactedExport(exportKind, exportTargetId.trim(), headers()),
                      (body) => {
                        setRedactedExportBody(body);
                        setFullExportBody(null);
                      },
                      `Redacted Export für ${exportKind}:${exportTargetId.trim()} geladen.`,
                    );
                  }}
                >
                  Redacted laden
                </button>

                {isSuperadmin ? (
                  <button
                    type="button"
                    className="ltc-btn ltc-btn--ghost"
                    disabled={busyKey === "export:grant"}
                    onClick={() => {
                      if (exportTargetId.trim().length === 0) {
                        setError("Ziel-ID ist erforderlich.");
                        setErrorField("exportTarget");
                        setNotice("");
                        exportTargetRef.current?.focus();
                        return;
                      }
                      const ttl = Number.parseInt(exportTtlSeconds, 10);
                      if (!Number.isFinite(ttl)) {
                        setError("TTL muss numerisch sein.");
                        setErrorField("exportTtl");
                        setNotice("");
                        exportTtlRef.current?.focus();
                        return;
                      }
                      void runAction(
                        "export:grant",
                        () => requestFullExportGrant(exportKind, exportTargetId.trim(), ttl, headers()),
                        (body) => {
                          setExportGrant(body);
                          setFullExportBody(null);
                        },
                        `One-time Export-Grant für ${exportKind}:${exportTargetId.trim()} erstellt.`,
                      );
                    }}
                  >
                    Full Grant anfordern
                  </button>
                ) : null}

                {isSuperadmin ? (
                  <button
                    type="button"
                    className="ltc-btn ltc-btn--soft"
                    disabled={busyKey === "export:full" || !exportGrant}
                    onClick={() => {
                      if (exportTargetId.trim().length === 0) {
                        setError("Ziel-ID ist erforderlich.");
                        setErrorField("exportTarget");
                        setNotice("");
                        exportTargetRef.current?.focus();
                        return;
                      }
                      if (!exportGrant) {
                        setError("Bitte zuerst einen Full Grant anfordern.");
                        setNotice("");
                        return;
                      }
                      void runAction(
                        "export:full",
                        () => fetchFullExportCiphertext(exportKind, exportTargetId.trim(), exportGrant.export_token, headers()),
                        (body) => setFullExportBody(body),
                        `Voll-Export für ${exportKind}:${exportTargetId.trim()} geladen und Token verbraucht.`,
                      );
                    }}
                  >
                    Voll-Export laden
                  </button>
                ) : null}
              </div>
            </form>

            {!exportGrant && isSuperadmin ? (
              <p className="ltc-helper-text ltc-mt-4">Für den Voll-Export zuerst einen frischen Full Grant anfordern. Das Token ist one-time und nur kurz gültig.</p>
            ) : null}

            {exportGrant ? (
              <div className="ltc-quote ltc-quote--gold ltc-mt-4">
                <div className="ltc-quote__t">Aktiver Full-Grant</div>
                <div className="ltc-muted">
                  Header: <code>{exportGrant.header}</code> · Ablauf: {new Date(exportGrant.expires_at).toLocaleString("de-DE")} · TTL:{" "}
                  {exportGrant.ttl_seconds}s
                </div>
                <div className="ltc-meta ltc-wordbreak">
                  Token: <code>{exportGrant.export_token}</code>
                </div>
              </div>
            ) : null}

            {redactedExportBody ? (
              <details className="ltc-details" open>
                <summary>Redacted Payload</summary>
                <pre className="ltc-pre ltc-mt-4">
                  {prettyBody(redactedExportBody)}
                </pre>
              </details>
            ) : null}

            {fullExportBody ? (
              <details className="ltc-details" open>
                <summary>Full Export Ciphertext</summary>
                <pre className="ltc-pre ltc-mt-4">
                  {prettyBody(fullExportBody)}
                </pre>
              </details>
            ) : null}
          </section>
          </div>
          </div>
        </>
      ) : null}
    </main>
  );
}
