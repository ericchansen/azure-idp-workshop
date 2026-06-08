import { Route } from "@playwright/test";
import path from "path";
import { test, expect } from "./helpers";

const uploadFixturePath = path.join(process.cwd(), "samples", "invoice.pdf");
const batchUploadFixturePath = path.join(process.cwd(), "samples", "purchase-order.pdf");

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

const mockBatchResult = {
  result: {
    documents: [
      {
        sample: "contract.pdf",
        document_id: "doc-contract-001",
        cu_fields: {
          summary: "Professional services agreement for advisory support.",
          key_topics: "contract, services, obligations",
        },
        cu_duration_ms: 2400,
        search_duration_ms: 112,
        cu_trace: {
          url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/workshop_batch:analyze",
          method: "POST",
          response_status: 200,
          duration_ms: 2400,
        },
        search_trace: {
          url: "https://test.search.windows.net/indexes/workshop-search/docs/index",
          method: "POST",
          response_status: 200,
          duration_ms: 112,
        },
      },
      {
        sample: "invoice.pdf",
        document_id: "doc-invoice-001",
        cu_fields: {
          summary: "Invoice for consulting services.",
          key_topics: "invoice, services, billing",
        },
        cu_duration_ms: 1800,
        search_duration_ms: 98,
        cu_trace: {
          url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/workshop_batch:analyze",
          method: "POST",
          response_status: 200,
          duration_ms: 1800,
        },
        search_trace: {
          url: "https://test.search.windows.net/indexes/workshop-search/docs/index",
          method: "POST",
          response_status: 200,
          duration_ms: 98,
        },
      },
      {
        sample: "receipt.png",
        document_id: "doc-receipt-001",
        cu_fields: {
          summary: "Retail receipt for hardware purchases.",
          key_topics: "receipt, retail, purchase",
        },
        cu_duration_ms: 1600,
        search_duration_ms: 87,
        cu_trace: {
          url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/workshop_batch:analyze",
          method: "POST",
          response_status: 200,
          duration_ms: 1600,
        },
        search_trace: {
          url: "https://test.search.windows.net/indexes/workshop-search/docs/index",
          method: "POST",
          response_status: 200,
          duration_ms: 87,
        },
      },
    ],
    summary: {
      total: 3,
      succeeded: 3,
      failed: 0,
      total_cu_ms: 5800,
      total_search_ms: 297,
      total_ms: 6097,
    },
  },
  trace: {
    ensure_index: {
      url: "https://test.search.windows.net/indexes/workshop-search",
      method: "PUT",
      response_status: 200,
      duration_ms: 91,
    },
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

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // Both result sections should appear
    await expect(
      page.getByText("Document Intelligence — Layout")
    ).toBeVisible();
    await expect(
      page.getByText("Content Understanding — Layout")
    ).toBeVisible();

    // Prebuilt field extraction section should appear
    await expect(
      page.getByText("Field Extraction").first()
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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // API trace toggle should exist
    await expect(page.getByText("API Trace").first()).toBeVisible();
  });

  test("variation samples highlight the layout fallback path", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout*", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout*", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
    await page.route("**/api/di/prebuilt/prebuilt-layout*", (route) =>
      mockRoute(route, {
        result: {
          content: "Structured purchase order",
          documents: [],
        },
        trace: {
          url: "https://test.cognitiveservices.azure.com/documentintelligence/documentModels/prebuilt-layout:analyze",
          method: "POST",
          response_status: 200,
          duration_ms: 1111,
        },
      })
    );

    await page.goto("/module/1");
    await expect(page.getByRole("button", { name: /Purchase Order A/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Vendor Intake B/i })).toBeVisible();

    await page.getByRole("button", { name: /Purchase Order B/i }).click();
    await expect(page.getByText("Sample focus")).toContainText("Purchase Order B");

    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(
      page.getByText("DI Layout Fallback - Normalize the Form")
    ).toBeVisible();
    await expect(
      page.getByText("No typed fields is the expected outcome here.")
    ).toBeVisible();
  });

  test("uploaded document is sent as multipart form data", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout", (route) =>
      mockRoute(route, mockCULayoutResult)
    );
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByLabel("Choose file").setInputFiles(uploadFixturePath);
    await expect(page.getByText("Selected:")).toBeVisible();

    const uploadRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/di/layout") && request.method() === "POST"
    );

    await page.getByRole("button", { name: /Run Analysis/i }).click();
    const uploadRequest = await uploadRequestPromise;
    expect(uploadRequest.headers()["content-type"]).toContain("multipart/form-data");

    await expect(
      page.getByText("Document Intelligence — Layout")
    ).toBeVisible();
    await expect(page.getByText("Analysis Failed")).not.toBeVisible();
  });

  test("uploaded CU markdown is sanitized before rendering", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/layout", (route) =>
      mockRoute(route, {
        result: {
          content: "<img src=x onerror=\"console.error('xss')\"># Safe content",
          contents: [{ markdown: "<img src=x onerror=\"console.error('xss')\"># Safe content" }],
        },
        trace: mockCULayoutResult.trace,
      })
    );
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByLabel("Choose file").setInputFiles(uploadFixturePath);
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    await expect(page.getByText("Content Understanding — Layout")).toBeVisible();
    const rendered = page.locator("[x-ref='cuRendered']");
    await expect(rendered.getByText("Safe content")).toBeVisible();
    await expect(rendered.locator("img[src='x']")).toHaveCount(0);
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

  test("uploaded document is sent to CU custom as multipart form data", async ({
    page, consoleErrors,
  }) => {
    await page.route("**/api/di/layout", (route) =>
      mockRoute(route, mockDILayoutResult)
    );
    await page.route("**/api/cu/custom", (route) =>
      mockRoute(route, mockCUCustomResult)
    );

    await page.goto("/module/2");
    await page.getByLabel("Choose file").setInputFiles(uploadFixturePath);
    await expect(page.getByText("Selected:")).toBeVisible();

    const cuRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/cu/custom") && request.method() === "POST"
    );

    await page.getByRole("button", { name: /Compare|Analyze|Run/i }).click();
    const cuRequest = await cuRequestPromise;
    expect(cuRequest.headers()["content-type"]).toContain("multipart/form-data");

    await expect(
      page.getByText("CU — Semantic Extraction").first()
    ).toBeVisible();
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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockErrorRoute(route, "Internal Server Error")
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockErrorRoute(route, htmlError, 502, "text/html")
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Invoice" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockRoute(route, mockDIPrebuiltResult)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

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
    await page.route("**/api/di/prebuilt/*", (route) =>
      mockErrorRoute(route, "DI service is down", 500)
    );

    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await page.getByRole("button", { name: /Run Analysis/i }).click();

    // CU should render content
    await expect(
      page.getByText("Content Understanding — Layout")
    ).toBeVisible();
    // DI should show error
    await expect(page.getByText("DI service is down").first()).toBeVisible();
  });
});

test.describe("Module 4 — Batch Workflow", () => {
  test("batch run shows summary, per-document results, and traces", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/batch/process", async (route) => {
      await delay(250);
      await mockRoute(route, mockBatchResult);
    });

    await page.goto("/module/4");

    const batchRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/batch/process") && request.method() === "POST"
    );

    await page.getByRole("button", { name: /Run Batch Pipeline/i }).click();

    await expect(page.getByText(/Processing\.\.\./)).toBeVisible();

    const batchRequest = await batchRequestPromise;
    expect(batchRequest.postDataJSON()).toEqual({
      samples: ["contract.pdf", "invoice.pdf", "receipt.png"],
    });

    await expect(page.getByText("Batch Complete")).toBeVisible();
    const contractCard = page.locator(".border.rounded-lg.p-4").filter({
      has: page.getByRole("heading", { name: "contract.pdf" }),
    });
    const invoiceCard = page.locator(".border.rounded-lg.p-4").filter({
      has: page.getByRole("heading", { name: "invoice.pdf" }),
    });
    const receiptCard = page.locator(".border.rounded-lg.p-4").filter({
      has: page.getByRole("heading", { name: "receipt.png" }),
    });

    await expect(contractCard).toContainText("Professional services agreement for advisory support.");
    await expect(invoiceCard).toContainText("Invoice for consulting services.");
    await expect(receiptCard).toContainText("Retail receipt for hardware purchases.");

    const traceDetails = page.locator("details", { hasText: "View API Traces" }).first();
    await traceDetails.locator("summary").click();
    await expect(traceDetails.getByText("CU Trace")).toBeVisible();
    await expect(traceDetails.getByText("Search Trace")).toBeVisible();
  });

  test("batch run with uploaded files uses multipart form data", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/batch/process", async (route) => {
      await delay(250);
      await mockRoute(route, {
        result: {
          documents: [
            ...mockBatchResult.result.documents,
            {
              sample: "invoice.pdf",
              source_type: "upload",
              document_id: "doc-upload-001",
              cu_fields: {
                summary: "Uploaded invoice for consulting services.",
                key_topics: "invoice, upload",
              },
              cu_duration_ms: 1200,
              search_duration_ms: 60,
              cu_trace: { response_status: 200, duration_ms: 1200 },
              search_trace: { response_status: 200, duration_ms: 60 },
            },
          ],
          summary: {
            total: 4,
            succeeded: 4,
            failed: 0,
            total_cu_ms: 7000,
            total_search_ms: 357,
            total_ms: 7357,
          },
        },
        trace: mockBatchResult.trace,
      });
    });

    await page.goto("/module/4");
    await page.getByLabel("Add files").setInputFiles(batchUploadFixturePath);
    await expect(page.getByText("Upload:")).toBeVisible();

    const batchRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/batch/process") && request.method() === "POST"
    );

    await page.getByRole("button", { name: /Run Batch Pipeline/i }).click();
    const batchRequest = await batchRequestPromise;
    expect(batchRequest.headers()["content-type"]).toContain("multipart/form-data");

    await expect(page.getByText("Batch Complete")).toBeVisible();
    await expect(page.getByText("Uploaded invoice for consulting services.")).toBeVisible();
  });
});
