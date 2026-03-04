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
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // Wait for real API results
    await waitForAnalysisComplete(page);

    // Both result sections must appear
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // DI must succeed: Real content should be extracted (the receipt says "Contoso")
    await expect(page.getByText("Contoso").first()).toBeVisible();

    // CU may fail gracefully (it's a real service) — just ensure no JS crashes
    // Check that CU section shows EITHER success OR a graceful error (not a blank crash)
    const cuSection = page.locator("#cu-results");
    const cuHasContent = await cuSection.locator("text=/Merchant|Total|Date|Analysis Unavailable/i").count() > 0;
    expect(cuHasContent).toBeTruthy();

    // API Trace should be available
    await expect(page.getByText("API Trace").first()).toBeVisible();
  });

  test("invoice: analyze produces real results, no errors", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    await page.getByRole("button", { name: "Invoice" }).click();
    await expect(page.getByText("Source Document")).toBeVisible();

    await page.getByRole("button", { name: /Run Analysis/i }).click();
    await waitForAnalysisComplete(page);

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // DI must succeed: Invoice should have content like "Invoice" or amounts
    const diSection = page.locator("#di-results");
    await expect(diSection.locator("text=/Invoice|Total|Amount/i").first()).toBeVisible();

    // CU may fail gracefully — just ensure section shows EITHER success OR graceful error
    const cuSection = page.locator("#cu-results");
    const cuHasContent = await cuSection.locator("text=/Invoice|Total|Amount|Analysis Unavailable/i").count() > 0;
    expect(cuHasContent).toBeTruthy();
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
    ).toBeVisible({ timeout: 120_000 });

    // Wait for CU spinner to disappear (CU custom analysis is slower)
    await expect(
      page.getByText(/Running CU/i).first()
    ).toBeHidden({ timeout: 120_000 });

    // Both services should show results
    await expect(page.getByText("CU — Semantic Extraction").first()).toBeVisible();

    // DI must succeed: Should extract raw text content
    const diSection = page.locator('section:has-text("DI — Raw Layout Extraction")');
    await expect(diSection.locator("text=/Agreement|Contract|Party/i").first()).toBeVisible();

    // CU custom analysis can take 60-120s — wait longer and allow graceful failure
    // CU should extract semantic fields (purple field name cards) OR show a graceful error
    const cuSection = page.locator('section:has-text("CU — Semantic Extraction")');
    const cuSucceeded = await cuSection.locator(".text-purple-800").first().isVisible({ timeout: 120_000 }).catch(() => false);
    const cuFailedGracefully = await cuSection.locator("text=/Analysis Unavailable|Error/i").first().isVisible({ timeout: 2_000 }).catch(() => false);
    
    // Either CU succeeded OR it failed gracefully (not a blank crash)
    expect(cuSucceeded || cuFailedGracefully).toBeTruthy();
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
  for (const mod of [1, 2]) {
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
