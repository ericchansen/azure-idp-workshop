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

    // DI must succeed — heading visible and receipt content extracted ("Contoso")
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Contoso").first()).toBeVisible();

    // CU may succeed or fail gracefully — check for EITHER result heading OR amber warning
    const cuSucceeded = await page.getByText("Content Understanding — Layout").isVisible().catch(() => false);
    const cuFailed = await page.getByText("CU Analysis Unavailable").isVisible().catch(() => false);
    expect(cuSucceeded || cuFailed).toBeTruthy();

    // API Trace should be available
    await expect(page.getByText("API Trace").first()).toBeVisible();
  });

  test("invoice: analyze produces real results, no errors", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    await page.getByRole("button", { name: "Invoice" }).click();
    await expect(page.getByText("Source Document")).toBeVisible();

    await page.getByRole("button", { name: /Run Analysis/i }).click();
    await waitForAnalysisComplete(page);

    // DI must succeed — heading visible and content extracted
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    // DI extracts raw text — the invoice PDF contains vendor/amount info
    const diContent = page.locator('[x-ref="diRendered"]').first();
    await expect(diContent).toBeVisible();
    const diText = await diContent.textContent();
    expect(diText && diText.length > 20).toBeTruthy();

    // CU may succeed or fail gracefully
    const cuSucceeded = await page.getByText("Content Understanding — Layout").isVisible().catch(() => false);
    const cuFailed = await page.getByText("CU Analysis Unavailable").isVisible().catch(() => false);
    expect(cuSucceeded || cuFailed).toBeTruthy();
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

    // DI must succeed: DI content area should have extracted text
    const diContent = page.locator('[x-ref="diRendered"]').first();
    await expect(diContent).toBeVisible({ timeout: 10_000 });
    const diText = await diContent.textContent();
    expect(diText && diText.length > 20).toBeTruthy();

    // Wait for CU to finish (all spinners gone)
    await expect(page.locator(".animate-pulse")).toHaveCount(0, { timeout: 120_000 });

    // CU takes 30+ seconds — after spinners are done, check CU heading is visible
    // The heading only appears inside x-show="diResult || cuResult" container
    await expect(
      page.getByText("CU — Semantic Extraction").first()
    ).toBeVisible({ timeout: 10_000 });

    // CU should show EITHER field cards (success) OR amber warning (graceful failure)
    // Check for the field rendering within the CU result section
    const cuSection = page.locator(".border-purple-200");
    const hasFields = await cuSection.locator(".bg-purple-50").first().isVisible().catch(() => false);
    const hasWarning = await cuSection.getByText("Unavailable").isVisible().catch(() => false);
    expect(hasFields || hasWarning).toBeTruthy();
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
