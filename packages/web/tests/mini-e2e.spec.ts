// packages/web/tests/mini-e2e.spec.ts
import { test, expect, Page } from "@playwright/test";

const DISCLAIMER_TEXT =
  "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

type GateMode = "me_401" | "me_200_consent_ok" | "me_403_consent_required" | "me_403_forbidden";

async function mockAppGateApi(page: Page, mode: GateMode) {
  let meCalls = 0;
  let consentCalls = 0;
  let authHeaderOnMe: string | null = null;

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") {
      meCalls += 1;
      authHeaderOnMe = route.request().headers()["authorization"] ?? null;

      if (mode === "me_401") return route.fulfill({ status: 401 });
      if (mode === "me_403_consent_required") return json(403, { detail: { code: "consent_required" } });
      if (mode === "me_403_forbidden") return json(403, { detail: { code: "forbidden" } });
      return json(200, { user_id: "u1", role: "user" });
    }

    if (path === "/api/consent/status") {
      consentCalls += 1;
      if (mode === "me_200_consent_ok") {
        return json(200, { is_complete: true, required: [], accepted: [] });
      }
      return json(403, { detail: { code: "consent_required" } });
    }

    if (path === "/api/vehicles") {
      return json(200, []);
    }

    if (path === "/api/vehicles/veh_test_1/trust-summary") {
      return json(200, {
        trust_light: "gruen",
        hint: "Dokumentation ist vollständig nachweisbar.",
        reason_codes: [],
        todo_codes: [],
        verification_level: "hoch",
        accident_status: "unfallfrei",
        accident_status_label: "Unfallfrei",
        history_status: "vorhanden",
        evidence_status: "vorhanden",
        top_trust_level: "T3",
      });
    }

    if (path === "/api/vehicles/veh_test_1/entries") {
      if (route.request().method() === "POST") {
        return json(201, {
          id: "entry_test_2",
          vehicle_id: "veh_test_1",
          entry_group_id: "entry_test_2",
          supersedes_entry_id: null,
          version: 1,
          revision_count: 1,
          is_latest: true,
          date: "2026-02-28",
          type: "Service",
          performed_by: "Eigenleistung",
          km: 125000,
          note: "Neuer Eintrag",
          cost_amount: 120.5,
          trust_level: "T2",
          created_at: "2026-02-28T12:00:00Z",
          updated_at: "2026-02-28T12:00:00Z",
        });
      }
      return json(200, [
        {
          id: "entry_test_1",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: null,
          version: 2,
          revision_count: 2,
          is_latest: true,
          date: "2026-02-20",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123456,
          note: "Große Inspektion durchgeführt",
          cost_amount: 499.9,
          trust_level: "T3",
          created_at: "2026-02-20T12:00:00Z",
          updated_at: "2026-02-21T12:00:00Z",
        },
      ]);
    }

    if (path === "/api/vehicles/veh_test_1/entries/entry_test_1/history") {
      return json(200, [
        {
          id: "entry_test_0",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: null,
          version: 1,
          revision_count: 2,
          is_latest: false,
          date: "2026-02-18",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123000,
          note: "Erste Fassung",
          cost_amount: 450,
          trust_level: "T2",
          created_at: "2026-02-18T10:00:00Z",
          updated_at: "2026-02-18T10:00:00Z",
        },
        {
          id: "entry_test_1",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: "entry_test_0",
          version: 2,
          revision_count: 2,
          is_latest: true,
          date: "2026-02-20",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123456,
          note: "Große Inspektion durchgeführt",
          cost_amount: 499.9,
          trust_level: "T3",
          created_at: "2026-02-20T12:00:00Z",
          updated_at: "2026-02-21T12:00:00Z",
        },
      ]);
    }

    if (path === "/api/vehicles/veh_test_1/entries/entry_test_1/revisions") {
      return json(201, {
        id: "entry_test_3",
        vehicle_id: "veh_test_1",
        entry_group_id: "grp_1",
        supersedes_entry_id: "entry_test_1",
        version: 3,
        revision_count: 3,
        is_latest: true,
        date: "2026-02-22",
        type: "Inspektion",
        performed_by: "Werkstatt",
        km: 123789,
        note: "Version 3",
        cost_amount: 525,
        trust_level: "T3",
        created_at: "2026-02-22T12:00:00Z",
        updated_at: "2026-02-22T12:00:00Z",
      });
    }

    if (path.startsWith("/api/vehicles/")) {
      return json(200, {
        id: "veh_test_1",
        vin_masked: "WAU********1234",
        nickname: "Demo Fahrzeug",
        meta: { nickname: "Demo Fahrzeug" },
      });
    }

    if (path === "/api/documents/admin/quarantine") {
      return json(403, { detail: "forbidden" });
    }

    if (path === "/api/documents/upload") {
      return json(200, {
        id: "doc_test_1",
        filename: "service.pdf",
        content_type: "application/pdf",
        size_bytes: 24,
        status: "QUARANTINED",
        scan_status: "PENDING",
        pii_status: "OK",
        created_at: "2026-02-28T12:00:00Z",
        created_by_user_id: "u1",
      });
    }

    if (path.startsWith("/api/documents/") && !path.endsWith("/download") && !path.endsWith("/approve") && !path.endsWith("/reject") && !path.endsWith("/scan")) {
      return json(200, {
        id: "doc_test_1",
        filename: "service.pdf",
        content_type: "application/pdf",
        size_bytes: 24,
        status: "QUARANTINED",
        scan_status: "PENDING",
        pii_status: "OK",
        created_at: "2026-02-28T12:00:00Z",
        created_by_user_id: "u1",
      });
    }

    if (path.startsWith("/api/public/qr/")) {
      return json(200, {
        trust_light: "gelb",
        hint: "Dokumentation vorhanden, aber Nachweise sind teilweise unvollständig.",
        history_status: "vorhanden",
        evidence_status: "nicht_vorhanden",
        verification_level: "mittel",
        accident_status: "unbekannt",
        accident_status_label: "Unbekannt",
        disclaimer: "",
      });
    }

    // fallback for unexpected calls (should not happen)
    return route.fallback();
  });

  return {
    get meCalls() {
      return meCalls;
    },
    get consentCalls() {
      return consentCalls;
    },
    get authHeaderOnMe() {
      return authHeaderOnMe;
    },
  };
}

async function boot(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForLoadState("domcontentloaded");
}

async function setHash(page: Page, hash: string): Promise<void> {
  await page.evaluate((h) => {
    window.location.hash = h;
  }, hash);
}

test("kein Token auf protected route => redirect #/auth?next=..., ohne /auth/me call", async ({ page }) => {
  const api = await mockAppGateApi(page, "me_200_consent_ok");
  await boot(page);

  await setHash(page, "#/vehicles?tab=all");

  await expect.poll(async () => page.evaluate(() => window.location.hash)).toMatch(/^#\/auth\?next=/);
  expect(api.meCalls).toBe(0);
  expect(api.consentCalls).toBe(0);
});

test("Token vorhanden => /auth/me mit Authorization Header + consent/status => ready", async ({ page }) => {
  const api = await mockAppGateApi(page, "me_200_consent_ok");

  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await boot(page);
  await setHash(page, "#/vehicles");

  // stays on vehicles (no redirect)
  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/vehicles");
  await expect(page.locator("main h1")).toContainText("Vehicles");

  expect(api.meCalls).toBeGreaterThan(0);
  expect(api.consentCalls).toBeGreaterThan(0);
  expect(api.authHeaderOnMe).toBe("Bearer tok_123");
});

test("Vehicle detail route loads real API-backed detail panel", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await mockAppGateApi(page, "me_200_consent_ok");
  await boot(page);
  await setHash(page, "#/vehicles/veh_test_1");

  await expect(page.locator("main h1")).toContainText("Vehicle Detail");
  await expect(page.locator("main")).toContainText("WAU********1234");
  await expect(page.locator("main")).toContainText("Demo Fahrzeug");
  await expect(page.locator("main")).toContainText("Große Inspektion durchgeführt");
  await expect(page.locator("main")).toContainText("v2 von 2");
});

test("Vehicle detail creates a revision and shows revision history", async ({ page }) => {
  let historyLoaded = false;
  let revisionCreated = false;

  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "u1", role: "user" });
    if (path === "/api/consent/status") return json(200, { is_complete: true, required: [], accepted: [] });
    if (path === "/api/vehicles/veh_test_1") {
      return json(200, {
        id: "veh_test_1",
        vin_masked: "WAU********1234",
        nickname: "Demo Fahrzeug",
        meta: { nickname: "Demo Fahrzeug" },
      });
    }
    if (path === "/api/vehicles/veh_test_1/trust-summary") {
      return json(200, {
        trust_light: "gruen",
        hint: "Dokumentation ist vollständig nachweisbar.",
        reason_codes: [],
        todo_codes: [],
        verification_level: "hoch",
        accident_status: "unfallfrei",
        accident_status_label: "Unfallfrei",
        history_status: "vorhanden",
        evidence_status: "vorhanden",
        top_trust_level: "T3",
      });
    }
    if (path === "/api/vehicles/veh_test_1/entries") {
      if (route.request().method() === "POST") {
        revisionCreated = true;
        return json(201, {
          id: "entry_test_3",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: "entry_test_1",
          version: 3,
          revision_count: 3,
          is_latest: true,
          date: "2026-02-22",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123789,
          note: "Version 3",
          cost_amount: 525,
          trust_level: "T3",
          created_at: "2026-02-22T12:00:00Z",
          updated_at: "2026-02-22T12:00:00Z",
        });
      }
      return json(200, [
        {
          id: revisionCreated ? "entry_test_3" : "entry_test_1",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: revisionCreated ? "entry_test_1" : null,
          version: revisionCreated ? 3 : 2,
          revision_count: revisionCreated ? 3 : 2,
          is_latest: true,
          date: revisionCreated ? "2026-02-22" : "2026-02-20",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: revisionCreated ? 123789 : 123456,
          note: revisionCreated ? "Version 3" : "Große Inspektion durchgeführt",
          cost_amount: revisionCreated ? 525 : 499.9,
          trust_level: "T3",
          created_at: "2026-02-22T12:00:00Z",
          updated_at: "2026-02-22T12:00:00Z",
        },
      ]);
    }
    if (path === "/api/vehicles/veh_test_1/entries/entry_test_1/revisions") {
      revisionCreated = true;
      return json(201, {
        id: "entry_test_3",
        vehicle_id: "veh_test_1",
        entry_group_id: "grp_1",
        supersedes_entry_id: "entry_test_1",
        version: 3,
        revision_count: 3,
        is_latest: true,
        date: "2026-02-22",
        type: "Inspektion",
        performed_by: "Werkstatt",
        km: 123789,
        note: "Version 3",
        cost_amount: 525,
        trust_level: "T3",
        created_at: "2026-02-22T12:00:00Z",
        updated_at: "2026-02-22T12:00:00Z",
      });
    }
    if (path === "/api/vehicles/veh_test_1/entries/entry_test_1/history") {
      historyLoaded = true;
      return json(200, [
        {
          id: "entry_test_0",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: null,
          version: 1,
          revision_count: 3,
          is_latest: false,
          date: "2026-02-18",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123000,
          note: "Erste Fassung",
          cost_amount: 450,
          trust_level: "T2",
          created_at: "2026-02-18T10:00:00Z",
          updated_at: "2026-02-18T10:00:00Z",
        },
        {
          id: "entry_test_1",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: "entry_test_0",
          version: 2,
          revision_count: 3,
          is_latest: false,
          date: "2026-02-20",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123456,
          note: "Große Inspektion durchgeführt",
          cost_amount: 499.9,
          trust_level: "T3",
          created_at: "2026-02-20T12:00:00Z",
          updated_at: "2026-02-21T12:00:00Z",
        },
        {
          id: "entry_test_3",
          vehicle_id: "veh_test_1",
          entry_group_id: "grp_1",
          supersedes_entry_id: "entry_test_1",
          version: 3,
          revision_count: 3,
          is_latest: true,
          date: "2026-02-22",
          type: "Inspektion",
          performed_by: "Werkstatt",
          km: 123789,
          note: "Version 3",
          cost_amount: 525,
          trust_level: "T3",
          created_at: "2026-02-22T12:00:00Z",
          updated_at: "2026-02-22T12:00:00Z",
        },
      ]);
    }

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/vehicles/veh_test_1");

  await page.getByRole("button", { name: "Versionshistorie laden" }).click();
  await expect.poll(() => historyLoaded).toBe(true);
  await expect(page.locator("main")).toContainText("v1");

  await page.getByRole("button", { name: "Neue Version anlegen" }).click();
  await page.getByLabel("Kilometerstand").fill("123789");
  await page.getByLabel("Bemerkung (optional)").fill("Version 3");
  await page.getByRole("button", { name: "Version speichern" }).click();

  await expect.poll(() => revisionCreated).toBe(true);
});

test("Documents route uploads a file and renders returned document metadata", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await mockAppGateApi(page, "me_200_consent_ok");
  await boot(page);
  await setHash(page, "#/documents");

  await page.locator("#documents-upload-input").setInputFiles({
    name: "service.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\n%%EOF\n", "utf8"),
  });
  await page.getByRole("button", { name: "Dokument hochladen" }).click();

  await expect(page.locator("main")).toContainText("service.pdf");
  await expect(page.locator("main")).toContainText("QUARANTINED");
  await expect(page.locator("main")).toContainText("PENDING");
});

test("Onboarding wizard creates vehicle and first entry via vehicle endpoints", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "u1", role: "user" });
    if (path === "/api/consent/status") return json(200, { is_complete: true, required: [], accepted: [] });
    if (path === "/api/vehicles" && route.request().method() === "POST") {
      return json(200, {
        id: "veh_new_1",
        vin_masked: "WAU********9999",
        nickname: null,
        meta: null,
      });
    }
    if (path === "/api/vehicles/veh_new_1/entries") {
      return json(201, {
        id: "entry_new_1",
        vehicle_id: "veh_new_1",
        entry_group_id: "entry_new_1",
        supersedes_entry_id: null,
        version: 1,
        revision_count: 1,
        is_latest: true,
        date: "2026-02-28",
        type: "Service",
        performed_by: "Eigenleistung",
        km: 120000,
        note: null,
        cost_amount: null,
        trust_level: null,
        created_at: "2026-02-28T12:00:00Z",
        updated_at: "2026-02-28T12:00:00Z",
      });
    }

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/onboarding");

  await page.getByLabel("VIN").fill("WAUZZZ1JZXW999999");
  await page.getByRole("button", { name: "Weiter" }).click();
  await page.getByRole("button", { name: "Fahrzeug speichern" }).click();
  await page.getByLabel("Kilometerstand").fill("120000");
  await page.getByRole("button", { name: "Entry speichern" }).click();

  await expect(page.locator("main")).toContainText("Geschafft");
  await expect(page.locator('a[href="#/vehicles/veh_new_1"]')).toHaveCount(2);
});

test("Auth page requests OTP, verifies login and forwards into consent flow", async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/request") {
      return json(200, {
        ok: true,
        challenge_id: "challenge-123",
        message: "Wenn die E-Mail-Adresse gültig ist, wurde ein Code gesendet.",
        dev_otp: "123456",
      });
    }

    if (path === "/api/auth/verify") {
      return json(200, {
        access_token: "tok_auth_1",
        expires_at: "2026-03-01T10:00:00Z",
      });
    }

    if (path === "/api/auth/me") {
      return json(200, { user_id: "u1", role: "user" });
    }

    if (path === "/api/consent/status") {
      return json(200, {
        is_complete: false,
        required: [
          { doc_type: "terms", doc_version: "v2" },
          { doc_type: "privacy", doc_version: "v3" },
        ],
        accepted: [],
      });
    }

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/auth?next=%23%2Fdocuments");

  await page.getByLabel("E-Mail").fill("vip@example.com");
  await page.getByRole("button", { name: "Code anfordern" }).click();

  await expect(page.locator('[data-testid="auth-challenge-id"]')).toHaveText("challenge-123");
  await expect(page.locator('[data-testid="auth-dev-otp"]')).toHaveText("123456");

  await page.getByLabel("OTP").fill("123456");
  await page.getByRole("button", { name: "Login verifizieren" }).click();

  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/consent?next=%23%2Fdocuments");
  await expect.poll(async () => page.evaluate(() => window.localStorage.getItem("ltc_auth_token_v1"))).toBe("tok_auth_1");
});

test("Auth page goes directly to target when consent is already complete", async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/request") {
      return json(200, {
        ok: true,
        challenge_id: "challenge-456",
        message: "Wenn die E-Mail-Adresse gültig ist, wurde ein Code gesendet.",
        dev_otp: "654321",
      });
    }

    if (path === "/api/auth/verify") {
      return json(200, {
        access_token: "tok_auth_2",
        expires_at: "2026-03-01T10:00:00Z",
      });
    }

    if (path === "/api/auth/me") {
      return json(200, { user_id: "u1", role: "user" });
    }

    if (path === "/api/consent/status") {
      return json(200, { is_complete: true, required: [], accepted: [] });
    }

    if (path === "/api/vehicles") return json(200, []);

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/auth?next=%23%2Fvehicles");

  await page.getByLabel("E-Mail").fill("vip@example.com");
  await page.getByRole("button", { name: "Code anfordern" }).click();
  await page.getByLabel("OTP").fill("654321");
  await page.getByRole("button", { name: "Login verifizieren" }).click();

  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/vehicles");
  await expect(page.locator("main h1")).toContainText("Vehicles");
});

test("Consent page accepts required versions and continues to target route", async ({ page }) => {
  let accepted = false;
  let acceptPayload: any = null;

  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "u1", role: "user" });

    if (path === "/api/consent/current") {
      return json(200, {
        required: [
          { doc_type: "terms", doc_version: "v2" },
          { doc_type: "privacy", doc_version: "v3" },
        ],
      });
    }

    if (path === "/api/consent/status") {
      if (accepted) {
        return json(200, {
          is_complete: true,
          required: [
            { doc_type: "terms", doc_version: "v2" },
            { doc_type: "privacy", doc_version: "v3" },
          ],
          accepted: [
            { doc_type: "terms", doc_version: "v2", accepted_at: "2026-02-28T12:00:00Z", source: "ui" },
            { doc_type: "privacy", doc_version: "v3", accepted_at: "2026-02-28T12:00:00Z", source: "ui" },
          ],
        });
      }

      return json(200, {
        is_complete: false,
        required: [
          { doc_type: "terms", doc_version: "v2" },
          { doc_type: "privacy", doc_version: "v3" },
        ],
        accepted: [],
      });
    }

    if (path === "/api/consent/accept") {
      acceptPayload = route.request().postDataJSON();
      accepted = true;
      return json(200, { ok: true });
    }

    if (path === "/api/vehicles") return json(200, []);

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/consent?next=%23%2Fvehicles");

  await expect(page.locator("main")).toContainText("v2");
  await expect(page.locator("main")).toContainText("v3");

  await page.getByLabel(/Terms/).check();
  await page.getByLabel(/Privacy/).check();
  await page.getByRole("button", { name: "Consent speichern" }).click();

  await expect.poll(() => accepted).toBe(true);
  expect(acceptPayload?.consents?.map((item: any) => `${item.doc_type}:${item.doc_version}`)).toEqual(["terms:v2", "privacy:v3"]);

  await page.getByRole("button", { name: "Weiter zum Zielbereich" }).click();
  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/vehicles");
});
test("/auth/me 403 consent_required => redirect #/consent with preserved next target", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await mockAppGateApi(page, "me_403_consent_required");
  await boot(page);

  await setHash(page, "#/vehicles");
  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/consent?next=%23%2Fvehicles");
});

test("/auth/me 403 without consent_required => forbidden UI", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await mockAppGateApi(page, "me_403_forbidden");
  await boot(page);

  await setHash(page, "#/vehicles");
  await expect(page.locator('[data-testid="forbidden-ui"]')).toHaveCount(1);
});

test("Trust Folders route loads with auth, consent and vehicle context", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "u1", role: "vip" });
    if (path === "/api/consent/status") return json(200, { is_complete: true, required: [], accepted: [] });
    if (path === "/api/trust/folders") {
      return json(200, [
        { id: 7, vehicle_id: "demo-1", owner_user_id: "u1", addon_key: "restauration", title: "Restauration 2026" },
      ]);
    }

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/trust-folders?vehicle_id=demo-1&addon_key=restauration");

  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe(
    "#/trust-folders?vehicle_id=demo-1&addon_key=restauration",
  );
  await expect(page.locator("main h1")).toContainText("Trust Folders");
  await expect(page.locator("main")).toContainText("Restauration 2026");
});

test("Trust Folders stay forbidden for plain user role", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "u1", role: "user" });
    if (path === "/api/consent/status") return json(200, { is_complete: true, required: [], accepted: [] });

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/trust-folders?vehicle_id=demo-1&addon_key=restauration");

  await expect(page.locator('[data-testid="forbidden-ui"]')).toHaveCount(1);
});

test("Admin route manages roles, VIP businesses and export grants", async ({ page }) => {
  let users = [
    { user_id: "uid-user-1", role: "user", created_at: "2026-02-28T10:00:00Z" },
    { user_id: "uid-mod-1", role: "user", created_at: "2026-02-28T09:00:00Z" },
  ];
  let businesses = [
    {
      business_id: "biz-demo-1",
      owner_user_id: "uid-owner-1",
      approved: false,
      created_at: "2026-02-28T10:30:00Z",
      approved_at: null,
      approved_by_user_id: null,
      staff_user_ids: [],
      staff_count: 0,
    },
  ];
  let grantIssued = false;
  let fullLoaded = false;

  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_admin");
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    if (path === "/api/auth/me") return json(200, { user_id: "sa-1", role: "superadmin" });
    if (path === "/api/consent/status") return json(200, { is_complete: true, required: [], accepted: [] });

    if (path === "/api/admin/users") return json(200, users);

    if (path === "/api/admin/users/uid-user-1/role") {
      users = users.map((item) => (item.user_id === "uid-user-1" ? { ...item, role: "vip" } : item));
      return json(200, {
        ok: true,
        user_id: "uid-user-1",
        old_role: "user",
        new_role: "vip",
        at: "2026-02-28T11:00:00Z",
      });
    }

    if (path === "/api/admin/vip-businesses" && route.request().method() === "GET") {
      return json(200, businesses);
    }

    if (path === "/api/admin/vip-businesses" && route.request().method() === "POST") {
      businesses = [
        {
          business_id: "biz-demo-1",
          owner_user_id: "uid-owner-1",
          approved: false,
          created_at: "2026-02-28T10:30:00Z",
          approved_at: null,
          approved_by_user_id: null,
          staff_user_ids: [],
          staff_count: 0,
        },
        ...businesses.filter((item) => item.business_id !== "biz-demo-1"),
      ];
      return json(200, {
        ok: true,
        business_id: "biz-demo-1",
        owner_user_id: "uid-owner-1",
        approved: false,
        created_at: "2026-02-28T10:30:00Z",
        approved_at: null,
        approved_by_user_id: null,
      });
    }

    if (path === "/api/admin/vip-businesses/biz-demo-1/approve") {
      businesses = businesses.map((item) =>
        item.business_id === "biz-demo-1"
          ? {
              ...item,
              approved: true,
              approved_at: "2026-02-28T11:05:00Z",
              approved_by_user_id: "sa-1",
            }
          : item,
      );
      return json(200, {
        ok: true,
        business_id: "biz-demo-1",
        owner_user_id: "uid-owner-1",
        approved: true,
        created_at: "2026-02-28T10:30:00Z",
        approved_at: "2026-02-28T11:05:00Z",
        approved_by_user_id: "sa-1",
      });
    }

    if (path === "/api/admin/vip-businesses/biz-demo-1/staff/uid-staff-1") {
      businesses = businesses.map((item) =>
        item.business_id === "biz-demo-1"
          ? {
              ...item,
              approved: true,
              approved_at: "2026-02-28T11:05:00Z",
              approved_by_user_id: "sa-1",
              staff_user_ids: ["uid-staff-1"],
              staff_count: 1,
            }
          : item,
      );
      return json(200, {
        ok: true,
        business_id: "biz-demo-1",
        user_id: "uid-staff-1",
        at: "2026-02-28T11:06:00Z",
      });
    }

    if (path === "/api/export/vehicle/veh-admin-1") {
      return json(200, {
        data: {
          target: "vehicle",
          id: "veh-admin-1",
          _redacted: true,
          vehicle: { public_id: "veh-admin-1" },
        },
      });
    }

    if (path === "/api/export/vehicle/veh-admin-1/grant") {
      grantIssued = true;
      return json(200, {
        vehicle_id: "veh-admin-1",
        export_token: "grant-token-1",
        token: "grant-token-1",
        expires_at: "2026-02-28T11:20:00Z",
        ttl_seconds: 300,
        one_time: true,
        header: "X-Export-Token",
      });
    }

    if (path === "/api/export/vehicle/veh-admin-1/full") {
      fullLoaded = true;
      expect(route.request().headers()["x-export-token"]).toBe("grant-token-1");
      return json(200, {
        vehicle_id: "veh-admin-1",
        ciphertext: "ciphertext-demo-1",
        alg: "fernet",
        one_time: true,
      });
    }

    return route.fallback();
  });

  await boot(page);
  await setHash(page, "#/admin");

  await expect(page.locator("main h1")).toContainText("Admin");
  await expect(page.locator('[data-testid="admin-page"]')).toContainText("uid-user-1");

  const userCard = page.locator("article").filter({ hasText: "uid-user-1" }).first();
  await userCard.getByLabel("Zielrolle").selectOption("vip");
  await userCard.getByRole("button", { name: "Rolle setzen" }).click();
  await expect(page.locator("main")).toContainText("wurde auf vip gesetzt");

  await page.getByLabel("Owner User-ID").fill("uid-owner-1");
  await page.getByLabel("Business-ID (optional)").fill("biz-demo-1");
  await page.getByRole("button", { name: "VIP-Business anlegen" }).click();
  await expect(page.locator("main")).toContainText("biz-demo-1");

  const businessCard = page.locator("article").filter({ hasText: "biz-demo-1" }).first();
  await businessCard.getByRole("button", { name: "Freigeben" }).click();
  await expect(page.locator("main")).toContainText("wurde freigegeben");

  await businessCard.getByLabel("Staff User-ID").fill("uid-staff-1");
  await businessCard.getByRole("button", { name: "Staff hinzufügen" }).click();
  await expect(page.locator("main")).toContainText("uid-staff-1");

  await page.getByLabel("Ziel-ID").fill("veh-admin-1");
  await page.getByRole("button", { name: "Redacted laden" }).click();
  await expect(page.locator("main")).toContainText("veh-admin-1");

  await page.getByRole("button", { name: "Full Grant anfordern" }).click();
  await expect.poll(() => grantIssued).toBe(true);
  await expect(page.locator("main")).toContainText("grant-token-1");

  await page.getByRole("button", { name: "Voll-Export laden" }).click();
  await expect.poll(() => fullLoaded).toBe(true);
  await expect(page.locator("main")).toContainText("ciphertext-demo-1");
});

test("Public QR shows disclaimer once (dedupe) and keeps exact text", async ({ page }) => {
  await mockAppGateApi(page, "me_401");
  await boot(page);

  await setHash(page, "#/public/qr/veh_test_1");

  const box = page.locator('section[aria-label="Trust-Ampel Hinweis"]');
  await expect(box).toHaveCount(1);
  await expect(box).toContainText(DISCLAIMER_TEXT);

  const hidden = page.locator('[data-testid="public-qr-disclaimer"]');
  await expect(hidden).toHaveCount(1);
  await expect(hidden).toHaveText(DISCLAIMER_TEXT);
});
