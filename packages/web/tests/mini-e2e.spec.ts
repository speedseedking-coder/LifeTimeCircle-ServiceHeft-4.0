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

    if (path.startsWith("/api/public/qr/")) {
      return json(200, { trust_light: "YELLOW", hint: "ok", disclaimer: "" });
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

test("/auth/me 403 consent_required => redirect #/consent", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("ltc_auth_token_v1", "tok_123");
  });

  await mockAppGateApi(page, "me_403_consent_required");
  await boot(page);

  await setHash(page, "#/vehicles");
  await expect.poll(async () => page.evaluate(() => window.location.hash)).toBe("#/consent");
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
