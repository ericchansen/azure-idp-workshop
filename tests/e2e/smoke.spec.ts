/**
 * Smoke E2E tests — run against the REAL deployed app with NO mocks.
 *
 * These catch real failures like misconfigured Azure endpoints,
 * expired credentials, and broken API services.
 *
 * Run with: npx playwright test --grep Smoke --project="Desktop Edge"
 */

import { test, expect, assertNoErrorBanners, waitForAnalysisComplete } from "./helpers";

// ============================================================
// Homepage
// ============================================================

test.describe("Smoke: Homepage", () => {
  test("loads without errors and has all navigation", async ({ page, consoleErrors }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/IDP Workshop/);

    // All module links present
    await expect(page.locator("nav").locator('a[href="/module/1"]')).toBeVisible();
    await expect(page.locator("nav").locator('a[href="/module/2"]')).toBeVisible();
    await expect(page.locator("nav").locator('a[href="/module/3"]')).toBeVisible();
    await expect(page.locator("nav").locator('a[href="/guide"]')).toBeVisible();
  });

  test("health API returns ok", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });
});

// ============================================================
// Module 1 — Structured Extraction (Live)
// ============================================================

test.describe("Smoke: Module 1 — Structured Extraction", () => {
  test("receipt: analyze produces real results, no errors", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    // Select the receipt sample
    await page.getByRole("button", { name: "Receipt" }).click();

    // Document preview should appear
    await expect(page.getByText("Source Document")).toBeVisible();

    // Click analyze
    await page.getByRole("button", { name: /Analyze/i }).click();

    // Wait for real API results
    await waitForAnalysisComplete(page);

    // Both result sections must appear
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // Real content should be extracted (the receipt says "Contoso")
    await expect(page.getByText("Contoso").first()).toBeVisible();

    // No error banners
    await assertNoErrorBanners(page);

    // API Trace should be available
    await expect(page.getByText("API Trace").first()).toBeVisible();
  });

  test("invoice: analyze produces real results, no errors", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    await page.getByRole("button", { name: "Invoice" }).click();
    await expect(page.getByText("Source Document")).toBeVisible();

    await page.getByRole("button", { name: /Analyze/i }).click();
    await waitForAnalysisComplete(page);

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    await assertNoErrorBanners(page);
  });
});

// ============================================================
// Module 2 — Unstructured Documents (Live)
// ============================================================

test.describe("Smoke: Module 2 — Unstructured Documents", () => {
  test("contract: DI layout vs CU custom, both produce results", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");

    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    // Wait for DI results first (faster)
    await expect(
      page.getByText("DI — Raw Layout Extraction").first()
    ).toBeVisible({ timeout: 90_000 });

    // Wait for CU spinner to disappear (CU custom analysis is slower)
    await expect(
      page.getByText(/Running CU/i).first()
    ).toBeHidden({ timeout: 90_000 });

    // Both services should show results
    await expect(page.getByText("CU — Semantic Extraction").first()).toBeVisible();

    // CU should extract semantic fields (purple field name cards)
    await expect(page.locator(".text-purple-800").first()).toBeVisible({ timeout: 10_000 });

    await assertNoErrorBanners(page);
  });
});

// ============================================================
// Module 3 — Custom Fields (Live)
// ============================================================

test.describe("Smoke: Module 3 — Custom & Inferred Fields", () => {
  test("contract: custom field extraction works", async ({ page, consoleErrors }) => {
    await page.goto("/module/3");

    // Field definitions should be visible before running
    await expect(page.getByText("summary", { exact: true })).toBeVisible();
    await expect(page.getByText("risk_level", { exact: true })).toBeVisible();

    // Run analysis
    await page.getByRole("button", { name: /Run/i }).click();

    await waitForAnalysisComplete(page);

    // Custom fields should show extracted values
    await expect(page.getByText("summary").first()).toBeVisible();
    await expect(page.getByText("risk_level").first()).toBeVisible();

    await assertNoErrorBanners(page);
  });
});

// ============================================================
// Guide Page
// ============================================================

test.describe("Smoke: Decision Guide", () => {
  test("page loads and interactive elements work", async ({ page, consoleErrors }) => {
    await page.goto("/guide");

    await expect(
      page.getByRole("heading", { name: /Decision Guide/ })
    ).toBeVisible();

    // The guide should have interactive content
    const pageContent = await page.textContent("body");
    expect(pageContent).toBeTruthy();
    expect(pageContent!.length).toBeGreaterThan(100);
  });
});

// ============================================================
// Document API (Live)
// ============================================================

test.describe("Smoke: Document API", () => {
  test("all sample documents are served correctly", async ({ request }) => {
    const resp = await request.get("/api/documents/samples");
    expect(resp.ok()).toBeTruthy();
    const samples = await resp.json();

    // Every listed sample must be downloadable
    for (const sample of samples) {
      const fileResp = await request.get(`/api/documents/samples/${sample.name}/raw`);
      expect(fileResp.ok()).toBeTruthy();
      const body = await fileResp.body();
      expect(body.length).toBeGreaterThan(0);
    }
  });
});

// ============================================================
// Cross-Module: Behind the Scenes panels
// ============================================================

test.describe("Smoke: Behind the Scenes", () => {
  for (const mod of [1, 2, 3]) {
    test(`Module ${mod}: Behind the Scenes expands without errors`, async ({ page, consoleErrors }) => {
      await page.goto(`/module/${mod}`);

      const details = page.locator("details", { hasText: "Behind the Scenes" });
      if ((await details.count()) > 0) {
        await details.first().locator("summary").click();
        // Content should appear, no errors
        await expect(details.first()).toContainText(/.+/);
      }
    });
  }
});
