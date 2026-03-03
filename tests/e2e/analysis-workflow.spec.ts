import { Route } from "@playwright/test";
import { test, expect } from "./helpers";

// --- Mock response fixtures ---

const mockDILayoutResult = {
  result: {
    content:
      "Contoso\n123 Main Street\nRedmond, WA 98052\n987-654-3210\n6/10/2019 13:59\nSales Associate: Paul\n2 Surface Pro 6 $1,998.00\n3 Surface Pen $299.97\nSub-Total $2,297.97\nTax $218.31\nTotal $2,516.28",
    pages: [
      {
        pageNumber: 1,
        words: [{ content: "Contoso", confidence: 0.99 }],
        lines: [{ content: "Contoso", spans: [] }],
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
    content:
      "Contoso\n123 Main Street\nRedmond, WA 98052\n987-654-3210\n6/10/2019 13:59",
    contents: [
      {
        markdown:
          "# Contoso\n\n123 Main Street\nRedmond, WA 98052\n\n987-654-3210",
      },
    ],
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
      summary: {
        value: "Professional services agreement between parties",
        confidence: 0.88,
      },
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

// --- Helpers ---

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

function mockErrorRoute(
  route: Route,
  body: string,
  status = 500,
  contentType = "text/plain"
) {
  return route.fulfill({ status, contentType, body });
}

// ============================================================
// Module 1 — Structured Extraction
// ============================================================

test.describe("Module 1 — Analysis Workflow", () => {
  test("analyze with mocked success shows DI and CU results", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // Both result sections should appear
    await expect(
      page.getByText("Document Intelligence — Layout")
    ).toBeVisible();
    await expect(
      page.getByText("Content Understanding — Layout")
    ).toBeVisible();

    // Results should contain extracted text (not error messages)
    await expect(page.getByText("Contoso").first()).toBeVisible();

    // No error banners should be present
    await expect(page.getByText("Analysis Failed")).not.toBeVisible();
  });

  test("analyze shows API trace section", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // API trace toggle should exist
    await expect(page.getByText("API Trace").first()).toBeVisible();
  });
});

// ============================================================
// Module 2 — Unstructured Documents (DI Layout vs CU Custom)
// ============================================================

test.describe("Module 2 — Analysis Workflow", () => {
  test("analyze contract shows DI layout vs CU custom extraction", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/custom*", (route) =>
      mockRoute(route, mockCUCustomResult)
    );

    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(
      page.getByText("DI — Raw Layout Extraction").first()
    ).toBeVisible();
    await expect(
      page.getByText("CU — Semantic Extraction").first()
    ).toBeVisible();

    // CU should show semantic fields that DI cannot extract
    const cuHeading = page.getByText("CU — Semantic Extraction").first();
    const cuResultPanel = cuHeading.locator("..").locator("..");
    await expect(cuResultPanel.getByText("summary").first()).toBeVisible();
    await expect(page.getByText("Analysis Failed")).not.toBeVisible();
  });
});

// ============================================================
// Error Resilience Tests
// ============================================================

test.describe("Error Resilience — Server Errors", () => {
  test("Module 1: 500 plain text shows actual error, not JSON parse error", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockErrorRoute(route, "Internal Server Error")
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockErrorRoute(route, "Internal Server Error")
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // Should show the actual error text, not "Unexpected token"
    await expect(page.getByText("Internal Server Error").first()).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });

  test("Module 1: HTML error page handled gracefully", async ({ page, consoleErrors }) => {
    const htmlError =
      "<html><body><h1>502 Bad Gateway</h1><p>nginx</p></body></html>";
    await page.route("**/api/di/layout*", (route) =>
      mockErrorRoute(route, htmlError, 502, "text/html")
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockErrorRoute(route, htmlError, 502, "text/html")
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // Should show error, not crash
    await expect(page.getByText("Analysis Failed").first()).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });

  test("Module 2: 500 plain text shows actual error", async ({ page, consoleErrors }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockErrorRoute(route, "Service Unavailable", 503)
    );
    await page.route("**/api/cu/custom*", (route) =>
      mockErrorRoute(route, "Service Unavailable", 503)
    );

    await page.goto("/module/2");
    await page.getByRole("button", { name: "Contract" }).click();
    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();

    await expect(page.getByText("Service Unavailable").first()).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });

});

test.describe("Error Resilience — Mixed Results", () => {
  test("Module 1: DI succeeds, CU fails — both render correctly", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockErrorRoute(route, "CU service is down", 500)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // DI should render content
    await expect(
      page.getByText("Document Intelligence — Layout")
    ).toBeVisible();
    // CU should show error
    await expect(page.getByText("CU service is down")).toBeVisible();
  });

  test("Module 1: CU succeeds, DI fails — both render correctly", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockErrorRoute(route, "DI service is down", 500)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Analyze with DI/i }).click();

    // CU should render content
    await expect(
      page.getByText("Content Understanding — Layout")
    ).toBeVisible();
    // DI should show error
    await expect(page.getByText("DI service is down")).toBeVisible();
  });
});
