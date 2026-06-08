import { Route } from "@playwright/test";
import path from "path";
import { test, expect } from "./helpers";

const uploadFixturePath = path.join(process.cwd(), "samples", "invoice.pdf");

function mockJsonRoute(
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

function mockTextRoute(
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

const initialStats = {
  result: {
    document_count: 2,
    storage_size: 2048,
  },
  trace: {
    url: "https://test.search.windows.net/indexes/workshop-search/stats",
    method: "GET",
    response_status: 200,
    duration_ms: 32,
  },
};

const ensureIndexResult = {
  result: {
    name: "workshop-search",
    fields: 9,
  },
  trace: {
    url: "https://test.search.windows.net/indexes/workshop-search",
    method: "PUT",
    response_status: 200,
    duration_ms: 85,
  },
};

const indexContractResult = {
  result: {
    cu_extraction: {
      fields: {
        summary: "Professional services agreement for advisory support.",
        key_topics: "contract, services, obligations",
      },
      content_preview: "This professional services agreement defines obligations and payment terms.",
    },
    indexing: {
      indexed: 1,
      total: 1,
    },
    document_id: "doc-contract-001",
  },
  trace: {
    cu: {
      url: "https://test.cognitiveservices.azure.com/contentunderstanding/analyzers/workshop-search:analyze",
      method: "POST",
      response_status: 200,
      duration_ms: 2400,
    },
    search: {
      url: "https://test.search.windows.net/indexes/workshop-search/docs/index",
      method: "POST",
      response_status: 200,
      duration_ms: 112,
    },
  },
};

const searchHitsResult = {
  result: {
    query: "service agreement obligations",
    total: 2,
    hits: [
      {
        id: "doc-contract-001",
        title: "contract.pdf",
        summary: "Professional services agreement for advisory support.",
        key_topics: "contract, services, obligations",
        source_doc: "contract.pdf",
        score: 41.25,
        reranker_score: 3.14,
        content_preview: "This professional services agreement defines obligations and payment terms.",
      },
      {
        id: "doc-invoice-001",
        title: "invoice.pdf",
        summary: "Invoice for consulting services.",
        key_topics: "invoice, services, billing",
        source_doc: "invoice.pdf",
        score: 30.5,
        reranker_score: 2.87,
        content_preview: "Invoice details for consulting services and payment dates.",
      },
    ],
  },
  trace: {
    url: "https://test.search.windows.net/indexes/workshop-search/docs/search",
    method: "POST",
    response_status: 200,
    duration_ms: 126,
  },
};

const emptySearchResult = {
  result: {
    query: "nothing indexed yet",
    total: 0,
    hits: [],
  },
  trace: {
    url: "https://test.search.windows.net/indexes/workshop-search/docs/search",
    method: "POST",
    response_status: 200,
    duration_ms: 101,
  },
};

test.describe("Module 3 — Search Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/search/stats", (route) =>
      mockJsonRoute(route, initialStats)
    );
  });

  test("page loads with document picker, disabled actions, and index stats", async ({
    page,
    consoleErrors,
  }) => {
    await page.goto("/module/3");

    await expect(
      page.getByRole("heading", { name: /Module 3: Document Search with AI/ })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /Contract/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Invoice/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Receipt/ })).toBeVisible();

    await expect(
      page.getByRole("button", { name: /Enrich & Index Document/i })
    ).toBeDisabled();
    await expect(page.getByRole("button", { name: /Search/ })).toBeDisabled();

    const statsBadge = page.locator("span").filter({ hasText: /Index:/ }).first();
    await expect(statsBadge).toContainText("2 document(s)");
  });

  test("indexing a document shows progress, traces, success details, and refreshed stats", async ({
    page,
    consoleErrors,
  }) => {
    let statsCalls = 0;
    await page.route("**/api/search/stats", (route) => {
      statsCalls += 1;
      return mockJsonRoute(route, {
        ...initialStats,
        result: {
          document_count: statsCalls > 1 ? 3 : 2,
          storage_size: 2048,
        },
      });
    });
    await page.route("**/api/search/ensure-index", (route) =>
      mockJsonRoute(route, ensureIndexResult)
    );
    await page.route("**/api/search/index", async (route) => {
      await delay(250);
      await mockJsonRoute(route, indexContractResult);
    });

    await page.goto("/module/3");
    await page.getByRole("button", { name: /Contract/ }).click();

    const indexButton = page.getByRole("button", { name: /Enrich & Index Document/i });
    await expect(indexButton).toBeEnabled();

    const indexRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/search/index") && request.method() === "POST"
    );

    await indexButton.click();

    await expect(page.getByText(/Enriching & Indexing/)).toBeVisible();
    const indexRequest = await indexRequestPromise;
    expect(indexRequest.postDataJSON()).toEqual({ sample: "contract.pdf" });

    await expect(page.getByText("✅ Document Indexed")).toBeVisible();
    await expect(page.getByText("Professional services agreement for advisory support.")).toBeVisible();
    await expect(page.getByText("doc-contract-001")).toBeVisible();
    await expect(page.getByText("What to Notice")).toBeVisible();

    const statsBadge = page.locator("span").filter({ hasText: /Index:/ }).first();
    await expect(statsBadge).toContainText("3 document(s)");

    const traces = page.locator("details", { hasText: "View API Traces" }).first();
    await traces.locator("summary").click();
    await expect(traces.getByText("CU Trace")).toBeVisible();
    await expect(traces.getByText("Search Trace")).toBeVisible();
  });

  test("uploading and indexing a document sends multipart form data", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/search/ensure-index", (route) =>
      mockJsonRoute(route, ensureIndexResult)
    );
    await page.route("**/api/search/index", async (route) => {
      await delay(250);
      await mockJsonRoute(route, {
        ...indexContractResult,
        result: {
          ...indexContractResult.result,
          document_id: "doc-upload-001",
          source_doc: "invoice.pdf",
          source_type: "upload",
        },
      });
    });

    await page.goto("/module/3");
    await page.getByLabel("Choose file").setInputFiles(uploadFixturePath);
    await expect(page.getByText("Selected:")).toBeVisible();

    const indexButton = page.getByRole("button", { name: /Enrich & Index Document/i });
    await expect(indexButton).toBeEnabled();

    const indexRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/search/index") && request.method() === "POST"
    );

    await indexButton.click();
    const indexRequest = await indexRequestPromise;
    expect(indexRequest.headers()["content-type"]).toContain("multipart/form-data");

    await expect(page.getByText("✅ Document Indexed")).toBeVisible();
    await expect(page.getByText("doc-upload-001")).toBeVisible();
  });

  test("indexing failure shows the actual server error instead of a JSON parse error", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/search/ensure-index", (route) =>
      mockJsonRoute(route, ensureIndexResult)
    );
    await page.route("**/api/search/index", (route) =>
      mockTextRoute(route, "Service Unavailable", 503)
    );

    await page.goto("/module/3");
    await page.getByRole("button", { name: /Receipt/ }).click();
    await page.getByRole("button", { name: /Enrich & Index Document/i }).click();

    await expect(page.getByText("❌ Indexing Failed")).toBeVisible();
    await expect(page.getByText("Service Unavailable")).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });

  test("search button submits a semantic query and renders result cards with scores and trace", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/search/query", (route) =>
      mockJsonRoute(route, searchHitsResult)
    );

    await page.goto("/module/3");

    const queryInput = page.getByPlaceholder("e.g. service agreement obligations");
    await queryInput.fill("service agreement obligations");
    await expect(page.getByRole("button", { name: /Search/ })).toBeEnabled();

    const searchRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/search/query") && request.method() === "POST"
    );

    await page.getByRole("button", { name: /Search/ }).click();

    const searchRequest = await searchRequestPromise;
    const searchPayload = searchRequest.postDataJSON();
    expect(searchPayload).toEqual({
      query: "service agreement obligations",
      top: 5,
      use_semantic: true,
      upload_scope: expect.any(String),
    });
    expect(searchPayload.upload_scope.length).toBeGreaterThan(10);

    await expect(page.getByText("🔎 Results — 2 hit(s)")).toBeVisible();

    const contractHit = page
      .locator(".border.border-gray-200.rounded-lg.p-4")
      .filter({ hasText: "contract.pdf" })
      .first();
    await expect(contractHit).toContainText("contract.pdf");
    await expect(contractHit).toContainText("Professional services agreement for advisory support.");
    await expect(contractHit).toContainText("Score: 41.25");
    await expect(contractHit).toContainText("Semantic: 3.14");

    const invoiceHit = page
      .locator(".border.border-gray-200.rounded-lg.p-4")
      .filter({ hasText: "invoice.pdf" })
      .first();
    await expect(invoiceHit).toContainText("Invoice for consulting services.");

    const trace = page.locator("details", { hasText: "View API Trace" }).first();
    await trace.locator("summary").click();
    await expect(trace.locator("pre")).toBeVisible();
  });

  test("pressing Enter runs search and renders the empty-state guidance", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/search/query", (route) =>
      mockJsonRoute(route, emptySearchResult)
    );

    await page.goto("/module/3");

    const queryInput = page.getByPlaceholder("e.g. service agreement obligations");
    await queryInput.fill("nothing indexed yet");

    const searchRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/search/query") && request.method() === "POST"
    );

    await queryInput.press("Enter");
    await searchRequestPromise;

    await expect(page.getByText("🔎 Results — 0 hit(s)")).toBeVisible();
    await expect(
      page.getByText("No results found. Try indexing some documents first, then search for concepts in them.")
    ).toBeVisible();
  });

  test("search failure shows the plain-text backend error without crashing the page", async ({
    page,
    consoleErrors,
  }) => {
    await page.route("**/api/search/query", (route) =>
      mockTextRoute(route, "Gateway Timeout", 504)
    );

    await page.goto("/module/3");
    await page.getByPlaceholder("e.g. service agreement obligations").fill("contract");
    await page.getByRole("button", { name: /Search/ }).click();

    await expect(page.getByText("❌ Search Failed")).toBeVisible();
    await expect(page.getByText("Gateway Timeout")).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });

  test("security best practices section is present and interactive", async ({
    page,
    consoleErrors,
  }) => {
    await page.goto("/module/3");

    // Security section is collapsible — summary should be visible
    const securityDetails = page.locator("details", {
      hasText: /Security Best Practices/,
    });
    const securitySummary = securityDetails.locator("summary");
    await expect(securitySummary).toBeVisible();

    // Expand the section
    await securitySummary.click();

    // Workshop vs Production comparison table
    await expect(
      securityDetails.getByText("Workshop vs. Production")
    ).toBeVisible();
    await expect(securityDetails.getByText("Private endpoint + VNet integration")).toBeVisible();

    // RBAC vs API Keys subsection
    await expect(securityDetails.getByText("RBAC vs. API Keys")).toBeVisible();
    await expect(
      securityDetails.getByText("Search Index Data Contributor", { exact: true })
    ).toBeVisible();

    // Managed Identity subsection
    await expect(securityDetails.getByText("System-Assigned")).toBeVisible();
    await expect(securityDetails.getByText("User-Assigned")).toBeVisible();

    // Network Isolation subsection
    await expect(securityDetails.getByText("Network Isolation")).toBeVisible();

    // Encryption subsection
    await expect(
      securityDetails.getByRole("heading", { name: "Customer-Managed Keys (CMK)" })
    ).toBeVisible();

    // IaC tabs: Bicep code is visible by default
    await expect(securityDetails.locator("pre", { hasText: /disableLocalAuth: true/ })).toBeVisible();

    // Switch to Terraform tab
    await securityDetails.getByRole("button", { name: "Terraform" }).click();
    await expect(
      securityDetails.locator("pre", { hasText: /local_authentication_enabled/ })
    ).toBeVisible();
  });
});
