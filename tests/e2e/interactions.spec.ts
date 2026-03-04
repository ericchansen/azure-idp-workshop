/**
 * Comprehensive UI interaction tests — every button, toggle, tab, and interactive element.
 *
 * These use mocked API responses to test UI behavior exhaustively.
 */

import { Route } from "@playwright/test";
import { test, expect } from "./helpers";

// --- Mock response fixtures (same as analysis-workflow.spec.ts) ---

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
    fields: {
      VendorName: { value: "Contoso", confidence: 0.95 },
      InvoiceTotal: { value: 2516.28, confidence: 0.92 },
    },
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-invoice:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 1500,
  },
};

const mockCUPrebuiltResult = {
  result: {
    content: "Contoso invoice",
    fields: {
      VendorName: { value: "Contoso", confidence: 0.93 },
      InvoiceTotal: { value: 2516.28, confidence: 0.91 },
    },
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/prebuilt-invoice:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 1100,
  },
};

const mockCUCustomResult = {
  result: {
    content: "Contract for professional services...",
    fields: {
      summary: { value: "Professional services agreement", confidence: 0.88 },
      risk_level: { value: "Medium", confidence: 0.82 },
    },
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/workshopContract:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 2000,
  },
};

// Error fixtures with trace data (for error state API Trace toggle tests)
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

const mockCUContentEmptyError = {
  result: {},
  trace: {
    url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/prebuilt-layout:analyze",
    method: "POST",
    response_status: 500,
    duration_ms: 1234,
    error: '(InvalidRequest) Invalid request. Code: InvalidRequest Message: Invalid request. Inner error: { "code": "ContentEmpty", "message": "No fields were extracted because the content is empty." }',
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
// Module 1 — Formatted/Raw Toggle
// ============================================================

test.describe("Module 1 — UI Interactions", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
  });

  test("Formatted/Raw toggle switches DI result view", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // Wait for results
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    // Formatted view visible by default, raw hidden
    const diRendered = page.locator("[x-ref='diRendered']");
    const diRaw = page.locator("[x-ref='diRaw']");
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();

    // Click Raw button
    await page.locator("button", { hasText: "{ } Raw" }).first().click();
    await expect(diRaw).toBeVisible();
    await expect(diRendered).not.toBeVisible();

    // Click Formatted to switch back
    await page.locator("button", { hasText: "Formatted" }).first().click();
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();
  });

  test("API Trace details toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    // Click "View API Trace" for DI
    const diTrace = page.locator("details", { hasText: "View API Trace" }).first();
    await diTrace.locator("summary").click();

    // Trace data should be visible (scope to the expanded trace details, not code examples)
    const traceContent = diTrace.locator("pre");
    await expect(traceContent.first()).toBeVisible();
  });

  test("timing and page count are displayed", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    // Timing should show
    await expect(page.getByText("1234 ms")).toBeVisible();

    // Page count should show
    await expect(page.getByText("1 page(s)")).toBeVisible();
  });

  test("teaching point appears after both results", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // Teaching point should appear
    await expect(page.getByText("What to Notice")).toBeVisible();
    await expect(page.getByText("DI is built for structured")).toBeVisible();
  });

  test("Formatted/Raw toggle switches CU result view", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // CU Formatted view visible by default, raw hidden
    const cuRendered = page.locator("[x-ref='cuRendered']");
    const cuRaw = page.locator("[x-ref='cuRaw']");
    await expect(cuRendered).toBeVisible();
    await expect(cuRaw).not.toBeVisible();

    // Click CU Raw button (second "{ } Raw" button on the page)
    await page.locator("button", { hasText: "{ } Raw" }).nth(1).click();
    await expect(cuRaw).toBeVisible();
    await expect(cuRendered).not.toBeVisible();

    // Click CU Formatted to switch back (second "Formatted" button)
    await page.locator("button", { hasText: "Formatted" }).nth(1).click();
    await expect(cuRendered).toBeVisible();
    await expect(cuRaw).not.toBeVisible();
  });

  test("CU API Trace details toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // Click "View API Trace" for CU (second trace toggle on the page)
    const cuTrace = page.locator("details", { hasText: "View API Trace" }).nth(1);
    await cuTrace.locator("summary").click();

    // CU trace data should be visible (scope to the expanded trace details)
    const traceContent = cuTrace.locator("pre");
    await expect(traceContent.first()).toBeVisible();
  });

  test("DI table rendering shows table data", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();

    // Table section should appear
    await expect(page.getByText("Detected Tables")).toBeVisible();
    await expect(page.getByText("2 rows × 2 cols")).toBeVisible();
  });
});

// ============================================================
// Module 2 — Document Selection
// ============================================================

test.describe("Module 2 — UI Interactions", () => {
  test("selecting Contract shows contract document", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await expect(page.locator("[x-text='selectedSample']").getByText("contract.pdf")).toBeVisible();
  });

  test("analyze button is visible", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    const runButton = page.getByRole("button", { name: /Compare|Analyze|Run/i });
    await expect(runButton).toBeVisible();
  });

  test("document preview iframe loads", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await expect(page.getByText("Source Document")).toBeVisible();
    await expect(page.locator("iframe")).toBeVisible();
  });

  test("DI Formatted/Raw toggle switches result view", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/custom*", (route) =>
      mockRoute(route, mockCUCustomResult)
    );

    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("DI — Raw Layout Extraction").first()).toBeVisible();

    // Formatted view visible by default, raw hidden
    const diRendered = page.locator("[x-ref='diRendered']");
    const diRaw = page.locator("[x-ref='diRaw']");
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();

    // Click Raw button
    await page.locator("button", { hasText: "{ } Raw" }).first().click();
    await expect(diRaw).toBeVisible();
    await expect(diRendered).not.toBeVisible();

    // Click Formatted to switch back
    await page.locator("button", { hasText: "Formatted" }).first().click();
    await expect(diRendered).toBeVisible();
    await expect(diRaw).not.toBeVisible();
  });
});

// ============================================================
// Decision Guide — Comparison Matrix & Scenario Cards
// ============================================================

test.describe("Decision Guide — Static Content", () => {
  test("comparison matrix table is visible", async ({ page, consoleErrors }) => {
    await page.goto("/guide");

    await expect(page.getByText("Feature Comparison Matrix")).toBeVisible();
    // Table headers
    await expect(page.getByText("Document Intelligence").first()).toBeVisible();
    await expect(page.getByText("Content Understanding").first()).toBeVisible();
  });

  test("scenario cards are visible", async ({ page, consoleErrors }) => {
    await page.goto("/guide");

    await expect(page.getByText("Common Scenarios")).toBeVisible();
    await expect(page.getByText("Legal contracts")).toBeVisible();
    await expect(page.getByText("Call center recordings")).toBeVisible();
  });
});

// ============================================================
// Module 2 — API Trace & Teaching Point
// ============================================================

test.describe("Module 2 — API Trace & Teaching Point", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/custom*", (route) =>
      mockRoute(route, mockCUCustomResult)
    );
  });

  test("DI API Trace details toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("DI — Raw Layout Extraction").first()).toBeVisible();

    // Click DI API Trace (first trace toggle in results section)
    const diTrace = page.locator("details", { hasText: "API Trace" }).first();
    await diTrace.locator("summary").click();

    // Verify trace content is visible within the expanded details
    await expect(diTrace.locator("pre").first()).toBeVisible();
  });

  test("CU API Trace details toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("CU — Semantic Extraction").first()).toBeVisible();

    // Click CU API Trace (second trace toggle in results section)
    const cuTrace = page.locator("details", { hasText: "API Trace" }).nth(1);
    await cuTrace.locator("summary").click();

    // Verify trace content is visible within the expanded details
    await expect(cuTrace.locator("pre").first()).toBeVisible();
  });

  test("teaching point appears after both results", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("DI — Raw Layout Extraction").first()).toBeVisible();
    await expect(page.getByText("CU — Semantic Extraction").first()).toBeVisible();

    await expect(page.getByText("What to Notice")).toBeVisible();
  });
});

// ============================================================
// Error State — API Trace Toggles
// ============================================================

test.describe("Error State — API Trace Toggles", () => {
  test("Module 1: DI error trace toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDIErrorWithTrace)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // DI error banner should appear
    await expect(page.getByText("DI Analysis Failed")).toBeVisible();

    // Click API Trace inside the DI error banner
    const errorBanner = page.locator(".bg-red-50", { hasText: "DI Analysis Failed" });
    const errorTrace = errorBanner.locator("details", { hasText: "API Trace" });
    await errorTrace.locator("summary").click();

    // Trace data should be visible
    await expect(errorBanner.getByText("documentintelligence")).toBeVisible();
  });

  test("Module 1: CU error trace toggle expands and shows trace data", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCUContentEmptyError)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // CU error banner should appear
    await expect(page.getByText("CU Analysis Failed")).toBeVisible();

    // Click API Trace inside the CU error banner
    const errorBanner = page.locator(".bg-red-50", { hasText: "CU Analysis Failed" });
    const errorTrace = errorBanner.locator("details", { hasText: "API Trace" });
    await errorTrace.locator("summary").click();

    // Trace data should be visible
    await expect(errorBanner.getByText("contentunderstanding")).toBeVisible();
  });

});

// ============================================================
// Homepage — Navigation
// ============================================================

test.describe("Homepage — Navigation Interactions", () => {
  test("module cards link to correct pages", async ({ page, consoleErrors }) => {
    await page.goto("/");

    // Click Module 1 card (use main content area to avoid nav link ambiguity)
    await page.locator("main").getByRole("link", { name: /Module 1/ }).click();
    await expect(page).toHaveURL(/\/module\/1/);
    await expect(page.getByRole("heading", { name: /Structured Extraction/ })).toBeVisible();
  });

  test("Module 2 card navigates to /module/2", async ({ page, consoleErrors }) => {
    await page.goto("/");
    await page.locator("main").getByRole("link", { name: /Module 2/ }).click();
    await expect(page).toHaveURL(/\/module\/2/);
    await expect(page.getByRole("heading", { name: /Module 2.*Semantic/ })).toBeVisible();
  });

  test("Decision Guide card navigates to /guide", async ({ page, consoleErrors }) => {
    await page.goto("/");
    await page.locator("main").getByRole("link", { name: /Decision Guide/ }).click();
    await expect(page).toHaveURL(/\/guide/);
    await expect(page.getByRole("heading", { name: /Decision Guide/ })).toBeVisible();
  });

  test("IDP Workshop logo navigates to homepage", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.locator("nav").getByRole("link", { name: /IDP Workshop/ }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page).toHaveTitle(/IDP Workshop/);
  });

  test("all module cards and guide link are present", async ({ page, consoleErrors }) => {
    await page.goto("/");

    await expect(page.locator("main").getByRole("link", { name: /Module 1/ })).toBeVisible();
    await expect(page.locator("main").getByRole("link", { name: /Module 2/ })).toBeVisible();
    await expect(page.locator("main").getByRole("link", { name: /Decision Guide/ })).toBeVisible();
  });
});
