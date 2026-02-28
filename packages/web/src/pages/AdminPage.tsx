import { FormEvent, useEffect, useMemo, useState } from "react";
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
  requestFullExportGrant,
  setAdminUserRole,
  type AdminApiResult,
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

function sortUsers(rows: AdminUser[]): AdminUser[] {
  return [...rows].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
}

function sortBusinesses(rows: VipBusiness[]): VipBusiness[] {
  return [...rows].sort((a, b) => {
    if (a.approved !== b.approved) return a.approved ? 1 : -1;
    return a.created_at < b.created_at ? 1 : -1;
  });
}

function headers(): { headers: Record<string, string> } {
  return { headers: authHeaders(getAuthToken()) };
}

function extractErrorMessage(result: { status: number; error: string }): string {
  if (result.status === 0) return "Netzwerkfehler beim Laden der Admin-Daten.";
  if (result.status === 401) return "Session abgelaufen. Bitte erneut anmelden.";
  if (result.status === 403 && result.error === "superadmin_required") return "Diese Aktion ist nur für SUPERADMIN erlaubt.";
  if (result.status === 403 && result.error === "forbidden") return "Kein Zugriff auf diese Admin-Aktion.";
  if (result.status === 404 && result.error === "user_not_found") return "User-ID wurde nicht gefunden.";
  if (result.status === 404 && result.error === "business_not_found") return "Business-ID wurde nicht gefunden.";
  if (result.status === 409 && result.error === "staff_limit_reached") return "Für dieses VIP-Business sind keine weiteren Staff-Slots frei.";
  if (result.status === 400 && result.error === "business_not_approved") return "Staff kann erst nach SUPERADMIN-Freigabe hinzugefügt werden.";
  if (result.status === 400 && result.error === "invalid_role") return "Die Zielrolle ist ungültig.";
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
    <article className="ltc-card" style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div className="ltc-card__title" style={{ marginBottom: 6 }}>
            <code>{props.user.user_id}</code>
          </div>
          <div className="ltc-muted">
            Aktuelle Rolle: <strong>{props.user.role}</strong> · erstellt {new Date(props.user.created_at).toLocaleString("de-DE")}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 14, maxWidth: 520 }}>
        <label>
          Zielrolle
          <select
            value={props.currentRole}
            onChange={(e) => props.onRoleChange(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
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
            value={props.currentReason}
            onChange={(e) => props.onReasonChange(e.target.value)}
            placeholder="Wird nur als reason_provided auditiert"
            autoComplete="off"
            style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
          />
        </label>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
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
  return (
    <article className="ltc-card" style={{ marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div className="ltc-card__title" style={{ marginBottom: 6 }}>
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

      <div className="ltc-muted" style={{ marginTop: 8 }}>
        Staff ({props.business.staff_count}/2):{" "}
        {props.business.staff_user_ids.length > 0 ? props.business.staff_user_ids.map((id) => <code key={id}>{id} </code>) : "noch keiner"}
      </div>

      {props.actorRole === "superadmin" ? (
        <div style={{ display: "grid", gap: 10, marginTop: 14, maxWidth: 560 }}>
          <label>
            Staff User-ID
            <input
              value={props.staffDraft}
              onChange={(e) => props.onStaffDraftChange(e.target.value)}
              placeholder="bestehende auth_users user_id"
              autoComplete="off"
              style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
            />
          </label>

          <label>
            Grund (optional)
            <input
              value={props.staffReason}
              onChange={(e) => props.onStaffReasonChange(e.target.value)}
              placeholder="Wird nur als reason_provided auditiert"
              autoComplete="off"
              style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
            />
          </label>

          <div>
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

  const isSuperadmin = props.actorRole === "superadmin";
  const visibleUsers = useMemo(() => sortUsers(users), [users]);
  const visibleBusinesses = useMemo(() => sortBusinesses(vipBusinesses), [vipBusinesses]);

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

  async function runAction<T>(key: string, action: Promise<AdminApiResult<T>>, onSuccess: (body: T) => void, successMessage: string) {
    setBusyKey(key);
    setError("");
    setNotice("");
    const result = await action;
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
    <main style={{ padding: 12 }} data-testid="admin-page">
      <h1>Admin</h1>
      <p>Rollen, Moderator-Akkreditierung, VIP-Business-Freigaben und Export-Step-up auf den produktiven Server-Contracts.</p>

      {error ? <InlineErrorBanner message={error} /> : null}
      {notice ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <div className="ltc-muted">{notice}</div>
        </section>
      ) : null}

      {loading ? (
        <section className="ltc-card" style={{ marginTop: 16 }}>
          <div className="ltc-muted">Admin-Daten werden geladen...</div>
        </section>
      ) : null}

      {!loading ? (
        <>
          <section className="ltc-card" style={{ marginTop: 16 }}>
            <div className="ltc-card__title">Rollen & Moderator</div>
            <div className="ltc-muted">
              Der Server auditiert nur ID-bezogene Metadaten und `reason_provided`, keine Freitext-Begründungen.
            </div>
            {visibleUsers.length === 0 ? <p className="ltc-muted" style={{ marginTop: 12 }}>Keine Nutzer gefunden.</p> : null}
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
                  void runAction(
                    `role:${user.user_id}`,
                    setAdminUserRole(user.user_id, roleDrafts[user.user_id] ?? user.role, reasonDrafts[user.user_id] ?? "", headers()),
                    (body) => updateUserRole(user.user_id, body.new_role),
                    `Rolle für ${user.user_id} wurde auf ${roleDrafts[user.user_id] ?? user.role} gesetzt.`,
                  )
                }
                onAccreditModerator={() =>
                  void runAction(
                    `moderator:${user.user_id}`,
                    accreditModerator(user.user_id, reasonDrafts[user.user_id] ?? "", headers()),
                    (body) => updateUserRole(user.user_id, body.new_role),
                    `Moderator-Akkreditierung für ${user.user_id} abgeschlossen.`,
                  )
                }
              />
            ))}
          </section>

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <div className="ltc-card__title">VIP-Businesses</div>
            <div className="ltc-muted">
              Admin kann Requests anlegen. Freigabe und Staff-Zuordnung bleiben serverseitig auf SUPERADMIN begrenzt.
            </div>

            <form
              style={{ display: "grid", gap: 10, maxWidth: 620, marginTop: 14 }}
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                const ownerUserId = businessOwnerUserId.trim();
                if (ownerUserId.length < 8) {
                  setError("Owner User-ID ist zu kurz.");
                  return;
                }
                void runAction(
                  "business:create",
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
                  value={businessOwnerUserId}
                  onChange={(e) => setBusinessOwnerUserId(e.target.value)}
                  placeholder="bestehende auth_users user_id"
                  autoComplete="off"
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>

              <label>
                Business-ID (optional)
                <input
                  value={businessId}
                  onChange={(e) => setBusinessId(e.target.value)}
                  placeholder="externes Business-Kürzel oder leer für UUID"
                  autoComplete="off"
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>

              <label>
                Grund (optional)
                <input
                  value={businessReason}
                  onChange={(e) => setBusinessReason(e.target.value)}
                  placeholder="Wird nur als reason_provided auditiert"
                  autoComplete="off"
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>

              <div>
                <button type="submit" className="ltc-btn ltc-btn--primary" disabled={busyKey === "business:create"}>
                  VIP-Business anlegen
                </button>
              </div>
            </form>

            {visibleBusinesses.length === 0 ? <p className="ltc-muted" style={{ marginTop: 12 }}>Noch keine VIP-Businesses vorhanden.</p> : null}
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
                  void runAction(
                    `business:approve:${business.business_id}`,
                    approveVipBusiness(business.business_id, headers()),
                    () => {
                      void loadAll();
                    },
                    `VIP-Business ${business.business_id} wurde freigegeben.`,
                  )
                }
                onAddStaff={() =>
                  void runAction(
                    `business:staff:${business.business_id}`,
                    addVipBusinessStaff(
                      business.business_id,
                      staffDrafts[business.business_id] ?? "",
                      staffReasonDrafts[business.business_id] ?? "",
                      headers(),
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

          <section className="ltc-card" style={{ marginTop: 16 }}>
            <div className="ltc-card__title">Export-Step-up</div>
            <div className="ltc-muted">
              Redacted Exports sind für Admin und SUPERADMIN nutzbar. One-time Full Exports mit `X-Export-Token` bleiben strikt SUPERADMIN-only.
            </div>

            <form
              style={{ display: "grid", gap: 10, maxWidth: 620, marginTop: 14 }}
              onSubmit={(e) => e.preventDefault()}
            >
              <label>
                Zieltyp
                <select value={exportKind} onChange={(e) => setExportKind(e.target.value as ExportTargetKind)} style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}>
                  <option value="vehicle">vehicle</option>
                  <option value="user">user</option>
                  <option value="servicebook">servicebook</option>
                </select>
              </label>

              <label>
                Ziel-ID
                <input
                  value={exportTargetId}
                  onChange={(e) => setExportTargetId(e.target.value)}
                  placeholder="vehicle_id / user_id / servicebook_id"
                  autoComplete="off"
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>

              <label>
                TTL Sekunden (für Full Grant)
                <input
                  value={exportTtlSeconds}
                  onChange={(e) => setExportTtlSeconds(e.target.value)}
                  inputMode="numeric"
                  autoComplete="off"
                  style={{ display: "block", width: "100%", marginTop: 8, padding: 10 }}
                />
              </label>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="ltc-btn ltc-btn--primary"
                  disabled={busyKey === "export:redacted" || exportTargetId.trim().length === 0}
                  onClick={() =>
                    void runAction(
                      "export:redacted",
                      fetchRedactedExport(exportKind, exportTargetId.trim(), headers()),
                      (body) => {
                        setRedactedExportBody(body);
                        setFullExportBody(null);
                      },
                      `Redacted Export für ${exportKind}:${exportTargetId.trim()} geladen.`,
                    )
                  }
                >
                  Redacted laden
                </button>

                {isSuperadmin ? (
                  <button
                    type="button"
                    className="ltc-btn ltc-btn--ghost"
                    disabled={busyKey === "export:grant" || exportTargetId.trim().length === 0}
                    onClick={() => {
                      const ttl = Number.parseInt(exportTtlSeconds, 10);
                      if (!Number.isFinite(ttl)) {
                        setError("TTL muss numerisch sein.");
                        return;
                      }
                      void runAction(
                        "export:grant",
                        requestFullExportGrant(exportKind, exportTargetId.trim(), ttl, headers()),
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
                    disabled={busyKey === "export:full" || !exportGrant || exportTargetId.trim().length === 0}
                    onClick={() =>
                      void runAction(
                        "export:full",
                        fetchFullExportCiphertext(exportKind, exportTargetId.trim(), exportGrant?.export_token ?? "", headers()),
                        (body) => setFullExportBody(body),
                        `Voll-Export für ${exportKind}:${exportTargetId.trim()} geladen und Token verbraucht.`,
                      )
                    }
                  >
                    Voll-Export laden
                  </button>
                ) : null}
              </div>
            </form>

            {exportGrant ? (
              <div className="ltc-quote ltc-quote--gold" style={{ marginTop: 14 }}>
                <div className="ltc-quote__t">Aktiver Full-Grant</div>
                <div className="ltc-muted">
                  Header: <code>{exportGrant.header}</code> · Ablauf: {new Date(exportGrant.expires_at).toLocaleString("de-DE")} · TTL:{" "}
                  {exportGrant.ttl_seconds}s
                </div>
                <div className="ltc-meta" style={{ wordBreak: "break-all" }}>
                  Token: <code>{exportGrant.export_token}</code>
                </div>
              </div>
            ) : null}

            {redactedExportBody ? (
              <details className="ltc-details" open>
                <summary>Redacted Payload</summary>
                <pre className="ltc-pre" style={{ marginTop: 10 }}>
                  {prettyBody(redactedExportBody)}
                </pre>
              </details>
            ) : null}

            {fullExportBody ? (
              <details className="ltc-details" open>
                <summary>Full Export Ciphertext</summary>
                <pre className="ltc-pre" style={{ marginTop: 10 }}>
                  {prettyBody(fullExportBody)}
                </pre>
              </details>
            ) : null}
          </section>
        </>
      ) : null}
    </main>
  );
}
