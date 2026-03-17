/**
 * High-signal UI interaction tests — validates behavior, not element existence.
 *
 * Each test verifies a distinct interactive behavior using mocked API responses.
 * Duplicate toggle/tab/trace patterns have been consolidated to single tests.
 */

import { Route } from "@playwright/test";
import { test, expect } from "./helpers";

// --- Mock response fixtures ---

const mockDILayoutResult = {
  result: {
    content:
      "Contoso\n123 Main Street\nRedmond, WA 98052\n987-654-3210",
    pages: [
      {
        pageNumber: 1,
        words: [{ content: "Contoso", confidence: 0.99 }],
        lines: [{ content: "Contoso", spans: [] }],
      },
    ],
    tables: [
      {
        rowCount: 2,
        columnCount: 2,
        cells: [
          { rowIndex: 0, columnIndex: 0, content: "Item", kind: "columnHeader" },
          { rowIndex: 0, columnIndex: 1, content: "Price", kind: "columnHeader" },
          { rowIndex: 1, columnIndex: 0, content: "Surface Pro", kind: "content" },
          { rowIndex: 1, columnIndex: 1, content: "$999", kind: "content" },
        ],
      },
    ],
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-layout:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 1234,
  },
};

const mockCULayoutResult = {
  result: {
    content: "# Contoso\n\n123 Main Street\nRedmond, WA 98052",
    contents: [{ markdown: "# Contoso\n\n123 Main Street\nRedmond, WA 98052" }],
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/prebuilt-layout:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 987,
  },
};

const mockDIPrebuiltResult = {
  result: {
    content: "Contoso invoice",
    documents: [{
      fields: {
        VendorName: { content: "Contoso", confidence: 0.95 },
        InvoiceTotal: { content: "$2,516.28", valueCurrency: { amount: 2516.28 }, confidence: 0.92 },
      },
    }],
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-invoice:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 1500,
  },
};

const mockDIErrorWithTrace = {
  result: {},
  trace: {
    url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-layout:analyze",
    method: "POST",
    response_status: 500,
    duration_ms: 450,
    error: "Internal Server Error — DI service unavailable",
  },
};

function mockRoute(
  route: Route,
  body: object,
  status = 200,
  contentType = "application/json"
) {
  return route.fulfill({
    status,
    contentType,
    body: JSON.stringify(body),
  });
}

// ============================================================
// Module 1 — Result Rendering & Interactions
// ============================================================

test.describe("Module 1 — Result Interactions", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );
  });

  test("Formatted/Raw toggle switches result view", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    const diRendered = page.locator("[x-ref='diRendered']");
    const diRaw = page.locator("[x-ref='diRaw']");
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();

    await page.locator("button", { hasText: "{ } Raw" }).first().click();
    await expect(diRaw).toBeVisible();
    await expect(diRendered).not.toBeVisible();

    await page.locator("button", { hasText: "Formatted" }).first().click();
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();
  });

  test("timing and page count are displayed after analysis", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    await expect(page.getByText("1234 ms")).toBeVisible();
    await expect(page.getByText("1 page(s)")).toBeVisible();
  });

  test("DI table rendering shows structured table data", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    await expect(page.getByText("Detected Tables")).toBeVisible();
    await expect(page.getByText("2 rows × 2 cols")).toBeVisible();
  });

  test("prebuilt field extraction shows fields with confidence scores", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Field Extraction").first()).toBeVisible();

    const prebuiltSection = page.locator(".border-green-200").first();
    await expect(prebuiltSection.locator(".font-mono", { hasText: "VendorName" })).toBeVisible();
    await expect(prebuiltSection.locator(".font-mono", { hasText: "InvoiceTotal" })).toBeVisible();
    await expect(prebuiltSection.getByText("95%")).toBeVisible();
    await expect(prebuiltSection.getByText("92%")).toBeVisible();
  });
});

// ============================================================
// Module 2 — Field Editor
// ============================================================

test.describe("Module 2 — Field Editor", () => {
  test("add field button opens form and adds a custom field", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");

    await page.getByRole("button", { name: /Add custom field/i }).click();
    await page.getByPlaceholder("e.g. effective_date").fill("contract_date");
    await page.getByPlaceholder("What should CU extract?").fill("The date the contract takes effect");
    await page.getByRole("button", { name: "Add Field", exact: true }).click();

    await expect(page.getByText("contract_date")).toBeVisible();
    await expect(page.getByText("The date the contract takes effect")).toBeVisible();
  });
});

// ============================================================
// Error State — API Trace in Error Banners
// ============================================================

test.describe("Error State — API Trace", () => {
  test("error trace toggle expands and shows diagnostic data", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDIErrorWithTrace)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("DI Analysis Failed")).toBeVisible();

    const errorBanner = page.locator(".bg-red-50", { hasText: "DI Analysis Failed" });
    const errorTrace = errorBanner.locator("details", { hasText: "API Trace" });
    await errorTrace.locator("summary").click();
    await expect(errorBanner.getByText("documentintelligence")).toBeVisible();
  });
});

// ============================================================
// Homepage — Navigation
// ============================================================

test.describe("Homepage — Navigation", () => {
  test("module cards and logo navigate correctly", async ({ page, consoleErrors }) => {
    await page.goto("/");

    await page.locator("main").getByRole("link", { name: /Module 1/ }).click();
    await expect(page).toHaveURL(/\/module\/1/);
    await expect(page.getByRole("heading", { name: /Structured Extraction/ })).toBeVisible();

    await page.locator("nav").getByRole("link", { name: /IDP Workshop/ }).click();
    await expect(page).toHaveURL(/\/$/);

    await page.locator("main").getByRole("link", { name: /Module 2/ }).click();
    await expect(page).toHaveURL(/\/module\/2/);

    await page.locator("nav").getByRole("link", { name: /IDP Workshop/ }).click();

    await page.locator("main").getByRole("link", { name: /Decision Guide/ }).click();
    await expect(page).toHaveURL(/\/guide/);
  });
});
