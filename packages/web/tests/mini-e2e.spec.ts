import { test, expect, Page } from "@playwright/test";

const DISCLAIMER_TEXT =
  "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.";

async function mockApi(page: Page, mode: "unauth" | "auth_ok" | "consent_required") {
  await page.route("**/api/**", async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    function notFound() {
      return route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "not_found" } }),
      });
    }

    if (url.includes("/api/auth/me")) {
      if (mode === "unauth") {
        return route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({ detail: { code: "unauthorized" } }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "u_test", role: "user" }),
      });
    }

    if (url.includes("/api/consent/status")) {
      if (mode === "consent_required") {
        return route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({ detail: { code: "consent_required" } }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ is_complete: true }),
      });
    }

    if (url.includes("/api/vehicles") && method === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      });
    }

    if (url.includes("/api/public/qr/") && method === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          trust_light: "YELLOW",
          hint: "Test-Hinweis",
          disclaimer: DISCLAIMER_TEXT,
        }),
      });
    }

    return notFound();
  });
}

test("401 redirects to #/auth?next=... (hash router compatible)", async ({ page }) => {
  await mockApi(page, "unauth");
  await page.goto("/#/vehicles");
  await page.waitForTimeout(500);

  const hash = await page.evaluate(() => window.location.hash);
  expect(hash.startsWith("#/auth")).toBeTruthy();
  expect(hash.includes("next=")).toBeTruthy();
});

test("loop guard: already on #/auth does not rewrite hash", async ({ page }) => {
  await mockApi(page, "unauth");
  await page.goto("/#/auth");
  await page.waitForTimeout(500);

  const hash = await page.evaluate(() => window.location.hash);
  expect(hash).toBe("#/auth");
});

test("403 consent_required redirects to #/consent", async ({ page }) => {
  await mockApi(page, "consent_required");
  await page.goto("/#/vehicles");
  await page.waitForTimeout(500);

  const hash = await page.evaluate(() => window.location.hash);
  expect(hash).toBe("#/consent");
});

async function gotoPublicQr(page: Page, vehicleId: string): Promise<void> {
  const candidates = [
    `/#/public/qr/${encodeURIComponent(vehicleId)}`,
    `/#/public-qr/${encodeURIComponent(vehicleId)}`,
    `/#/publicqr/${encodeURIComponent(vehicleId)}`,
    `/#/public/${encodeURIComponent(vehicleId)}`,
  ];

  for (const path of candidates) {
    await page.goto(path);
    await page.waitForTimeout(200);
    const h1 = page.getByRole("heading", { name: "Public QR" });
    if (await h1.count()) return;
  }

  throw new Error("public_qr_route_not_found");
}

test("Public QR shows disclaimer once (dedupe) and keeps exact text", async ({ page }) => {
  await mockApi(page, "auth_ok");
  await gotoPublicQr(page, "veh_test_1");

  const loc = page.getByText(DISCLAIMER_TEXT, { exact: true });
  await expect(loc).toHaveCount(1);
});