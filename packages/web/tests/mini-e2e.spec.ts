import { test, expect, Page } from "@playwright/test";

const DISCLAIMER_TEXT =
  "Die Trust-Ampel bewertet ausschlieÃŸlich die Dokumentations- und NachweisqualitÃ¤t. Sie ist keine Aussage Ã¼ber den technischen Zustand des Fahrzeugs.";

/**
 * Mockt API-Responses fÃ¼r die E2E-Flows:
 * - /api/public/qr/:id wird von PublicQrPage genutzt
 * - /api/vehicles* bleibt als Fallback (kann je nach App-Aufruf auftreten)
 */
async function mockApi(page: Page, mode: "unauth" | "auth_ok" | "consent_required") {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });

    // --- Public QR endpoint (used by PublicQrPage) ---
    if (path.startsWith("/api/public/qr/")) {
      if (mode === "unauth") return route.fulfill({ status: 401 });
      if (mode === "consent_required") return json(403, { detail: { code: "consent_required" } });

      // auth_ok: payload fields that UI may touch
      return json(200, {
        vehicleId: path.split("/").pop(),
        ok: true,
        trust_light: "YELLOW",
        hint: "ok",
        disclaimer: "",
      });
    }

    // --- Vehicles fallback ---
    if (path.startsWith("/api/vehicles")) {
      if (mode === "unauth") return route.fulfill({ status: 401 });
      if (mode === "consent_required") return json(403, { detail: { code: "consent_required" } });
      return json(200, []);
    }

    return route.fallback();
  });
}

async function bootApp(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForLoadState("domcontentloaded");
}

async function setHash(page: Page, hash: string): Promise<void> {
  if (!hash.startsWith("#")) throw new Error(`hash must start with '#': ${hash}`);
  await page.evaluate((h) => {
    window.location.hash = h;
  }, hash);
}

test("401 redirects to #/auth?next=... (hash router compatible)", async ({ page }) => {
  await mockApi(page, "unauth");
  await bootApp(page);

  await setHash(page, "#/public/qr/demo");

  await expect
    .poll(async () => page.evaluate(() => window.location.hash), { timeout: 10_000 })
    .toMatch(/^#\/auth(\?|$)/);

  const hash = await page.evaluate(() => window.location.hash);
  expect(hash).toContain("next=");
});

test("loop guard: already on #/auth does not rewrite hash", async ({ page }) => {
  await mockApi(page, "unauth");
  await bootApp(page);

  await setHash(page, "#/auth");

  await expect
    .poll(async () => page.evaluate(() => window.location.hash), { timeout: 3_000 })
    .toBe("#/auth");
});

test("403 consent_required redirects to #/consent", async ({ page }) => {
  await mockApi(page, "consent_required");
  await bootApp(page);

  await setHash(page, "#/public/qr/demo");

  await expect
    .poll(async () => page.evaluate(() => window.location.hash), { timeout: 10_000 })
    .toBe("#/consent");
});

test("Public QR shows disclaimer once (dedupe) and keeps exact text", async ({ page }) => {
  await mockApi(page, "auth_ok");
  await bootApp(page);

  await setHash(page, "#/public/qr/veh_test_1");

  const loc = page.getByText(DISCLAIMER_TEXT, { exact: true });
  await expect(loc).toHaveCount(1);
});