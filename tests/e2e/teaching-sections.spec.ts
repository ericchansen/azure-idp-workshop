/**
 * E2E tests for educational teaching sections across Modules 1 and 2.
 *
 * Each module has:
 * 1. Architecture & Setup — expandable <details> with data flow, comparison boxes, Try It Yourself tabs, IaC tabs
 * 2. "What to Look For" callout — amber box before the analyze button
 * 3. Comparison Guide — sky box that appears after both results complete
 *
 * These use mocked API responses to test UI behavior.
 */

import { Route } from "@playwright/test";
import { test, expect } from "./helpers";

// --- Mock response fixtures ---

const mockDILayoutResult = {
  result: {
    content: "Contoso\n123 Main Street\nRedmond, WA 98052\n987-654-3210",
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
    content: "Contoso receipt",
    documents: [{
      fields: {
        MerchantName: { content: "Contoso", confidence: 0.95 },
        Total: { content: "$2,516.28", confidence: 0.92 },
      },
    }],
  },
  trace: {
    url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-receipt:analyze",
    method: "POST",
    response_status: 200,
    duration_ms: 1500,
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
// Module 1 — Teaching Sections
// ============================================================

test.describe("Module 1 — Architecture & Setup Section", () => {
  test("Architecture & Setup details element exists and can be expanded", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    const details = page.locator("details.bg-emerald-50");
    await expect(details).toBeVisible();

    // Initially collapsed — inner content not visible
    const innerContent = details.locator(".px-5.pb-5");
    await expect(innerContent).not.toBeVisible();

    // Click summary to expand
    await details.locator("summary").click();
    await expect(innerContent).toBeVisible();
  });

  test("Architecture section contains data flow diagram elements", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    // Expand the section
    await page.locator("details.bg-emerald-50 summary").click();

    // Data flow heading
    await expect(page.getByText("Data Flow")).toBeVisible();

    // Key diagram elements
    await expect(page.locator("details.bg-emerald-50").getByText("Browser", { exact: true })).toBeVisible();
    await expect(page.locator("details.bg-emerald-50").getByText("FastAPI", { exact: true })).toBeVisible();
    await expect(page.locator("details.bg-emerald-50").getByText("Azure AI Services", { exact: true })).toBeVisible();
  });

  test("Architecture section contains 'What Are We Comparing' content", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.locator("details.bg-emerald-50 summary").click();

    await expect(page.getByText("What Are We Comparing?")).toBeVisible();
    await expect(page.locator("details.bg-emerald-50").getByText("Document Intelligence (DI)")).toBeVisible();
    await expect(page.locator("details.bg-emerald-50").getByText("Content Understanding (CU)")).toBeVisible();
  });

  test("Try It Yourself tabs switch between Python and cURL", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.locator("details.bg-emerald-50 summary").click();

    // Python tab active by default — Python code visible
    const archSection = page.locator("details.bg-emerald-50");
    const pythonContent = archSection.locator("[x-show=\"tryTab === 'python'\"]");
    const curlContent = archSection.locator("[x-show=\"tryTab === 'curl'\"]");
    await expect(pythonContent).toBeVisible();
    await expect(curlContent).not.toBeVisible();

    // Click cURL tab
    await archSection.getByRole("button", { name: /cURL/ }).click();
    await expect(curlContent).toBeVisible();
    await expect(pythonContent).not.toBeVisible();

    // Click Python tab to switch back
    await archSection.getByRole("button", { name: /Python/ }).click();
    await expect(pythonContent).toBeVisible();
    await expect(curlContent).not.toBeVisible();
  });

  test("IaC tabs switch between Bicep, Terraform, and CLI", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.locator("details.bg-emerald-50 summary").click();

    const archSection = page.locator("details.bg-emerald-50");
    const bicepContent = archSection.locator("[x-show=\"iacTab === 'bicep'\"]");
    const terraformContent = archSection.locator("[x-show=\"iacTab === 'terraform'\"]");
    const cliContent = archSection.locator("[x-show=\"iacTab === 'cli'\"]");

    // Bicep active by default
    await expect(bicepContent).toBeVisible();
    await expect(terraformContent).not.toBeVisible();
    await expect(cliContent).not.toBeVisible();

    // Click Terraform tab
    await archSection.getByRole("button", { name: "Terraform" }).click();
    await expect(terraformContent).toBeVisible();
    await expect(bicepContent).not.toBeVisible();
    await expect(cliContent).not.toBeVisible();

    // Click Azure CLI tab
    await archSection.getByRole("button", { name: "Azure CLI" }).click();
    await expect(cliContent).toBeVisible();
    await expect(bicepContent).not.toBeVisible();
    await expect(terraformContent).not.toBeVisible();

    // Back to Bicep
    await archSection.getByRole("button", { name: "Bicep" }).click();
    await expect(bicepContent).toBeVisible();
  });
});

test.describe("Module 1 — What to Look For & Comparison Guide", () => {
  test("'What to Look For' amber callout is visible", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");

    const amberBox = page.locator(".bg-amber-50");
    await expect(amberBox).toBeVisible();
    await expect(page.getByText("What to Look For")).toBeVisible();
  });

  test("Comparison Guide sky box appears after mocked analysis results", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");

    // Comparison guide should NOT be visible before analysis
    const comparisonGuide = page.locator(".bg-sky-50");
    await expect(comparisonGuide).not.toBeVisible();

    // Run analysis
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // Wait for both results
    await expect(page.getByText("Document Intelligence — Layout")).toBeVisible();
    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();

    // Comparison guide should now be visible
    await expect(comparisonGuide).toBeVisible();
    await expect(page.getByText("Side-by-Side Comparison Guide")).toBeVisible();
  });
});

// ============================================================
// Module 2 — Teaching Sections
// ============================================================

test.describe("Module 2 — Architecture & Setup Section", () => {
  test("Architecture & Setup details element exists and can be expanded", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");

    const details = page.locator("details.bg-emerald-50");
    await expect(details).toBeVisible();

    const innerContent = details.locator(".px-5.pb-5");
    await expect(innerContent).not.toBeVisible();

    await details.locator("summary").click();
    await expect(innerContent).toBeVisible();
  });

  test("Try It Yourself tabs switch between Python and cURL", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.locator("details.bg-emerald-50 summary").click();

    const archSection = page.locator("details.bg-emerald-50");
    const pythonContent = archSection.locator("[x-show=\"tryTab === 'python'\"]");
    const curlContent = archSection.locator("[x-show=\"tryTab === 'curl'\"]");
    await expect(pythonContent).toBeVisible();
    await expect(curlContent).not.toBeVisible();

    await archSection.getByRole("button", { name: /cURL/ }).click();
    await expect(curlContent).toBeVisible();
    await expect(pythonContent).not.toBeVisible();

    await archSection.getByRole("button", { name: /Python/ }).click();
    await expect(pythonContent).toBeVisible();
    await expect(curlContent).not.toBeVisible();
  });

  test("IaC tabs switch between Bicep, Terraform, and CLI", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await page.locator("details.bg-emerald-50 summary").click();

    const archSection = page.locator("details.bg-emerald-50");
    const bicepContent = archSection.locator("[x-show=\"iacTab === 'bicep'\"]");
    const terraformContent = archSection.locator("[x-show=\"iacTab === 'terraform'\"]");
    const cliContent = archSection.locator("[x-show=\"iacTab === 'cli'\"]");

    await expect(bicepContent).toBeVisible();

    await archSection.getByRole("button", { name: "Terraform" }).click();
    await expect(terraformContent).toBeVisible();
    await expect(bicepContent).not.toBeVisible();

    await archSection.getByRole("button", { name: "Azure CLI" }).click();
    await expect(cliContent).toBeVisible();
    await expect(terraformContent).not.toBeVisible();

    await archSection.getByRole("button", { name: "Bicep" }).click();
    await expect(bicepContent).toBeVisible();
  });
});

test.describe("Module 2 — What to Look For & Comparison Guide", () => {
  test("'What to Look For' amber callout is visible", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");

    const amberBox = page.locator(".bg-amber-50");
    await expect(amberBox).toBeVisible();
    await expect(page.getByText("What to Look For")).toBeVisible();
  });

  test("Comparison Guide sky box appears after mocked analysis results", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/custom*", (route) =>
      mockRoute(route, mockCUCustomResult)
    );

    await page.goto("/module/2");

    const comparisonGuide = page.locator(".bg-sky-50");
    await expect(comparisonGuide).not.toBeVisible();

    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("DI — Raw Layout Extraction").first()).toBeVisible();
    await expect(page.getByText("CU — Semantic Extraction").first()).toBeVisible();

    await expect(comparisonGuide).toBeVisible();
    await expect(page.getByText("Side-by-Side Comparison Guide")).toBeVisible();
  });
});
