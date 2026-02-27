import { test, expect } from "./helpers";

test.describe("Homepage", () => {
  test("loads and shows module cards", async ({ page, consoleErrors }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/IDP Workshop/);
    // Nav links exist
    await expect(
      page.locator("nav").locator('a[href="/module/1"]')
    ).toBeVisible();
    await expect(
      page.locator("nav").locator('a[href="/module/2"]')
    ).toBeVisible();
    await expect(
      page.locator("nav").locator('a[href="/module/3"]')
    ).toBeVisible();
    await expect(
      page.locator("nav").locator('a[href="/guide"]')
    ).toBeVisible();
  });

  test("health endpoint returns ok", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });
});

test.describe("Module 1 — Structured Extraction", () => {
  test("page loads with document picker", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await expect(
      page.getByRole("heading", { name: /Module 1.*Structured Extraction/ })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Invoice" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Receipt" })).toBeVisible();
  });

  test("selecting sample shows document preview", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    await page.getByRole("button", { name: "Receipt" }).click();
    await expect(page.getByText("Source Document")).toBeVisible();
  });

  test("Behind the Scenes panel expands", async ({ page, consoleErrors }) => {
    await page.goto("/module/1");
    const details = page.locator("details", {
      hasText: "Behind the Scenes",
    });
    await expect(details).toBeVisible();
    await details.locator("summary").click();
    await expect(page.getByText("Azure Resources Required")).toBeVisible();
    await expect(page.getByText("Python SDK Code")).toBeVisible();
    await expect(page.getByText("Pricing (per page)")).toBeVisible();
  });
});

test.describe("Module 2 — Unstructured Documents", () => {
  test("page loads with document picker", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    await expect(
      page.getByRole("heading", { name: /Module 2.*Unstructured/ })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Contract" })).toBeVisible();
  });

  test("Behind the Scenes panel works", async ({ page, consoleErrors }) => {
    await page.goto("/module/2");
    const details = page.locator("details", {
      hasText: "Behind the Scenes",
    });
    await details.locator("summary").click();
    await expect(page.getByText("REST API Endpoints")).toBeVisible();
  });
});

test.describe("Module 3 — Custom & Inferred Fields", () => {
  test("page loads with field definitions", async ({ page, consoleErrors }) => {
    await page.goto("/module/3");
    await expect(
      page.getByRole("heading", { name: /Module 3.*Custom/ })
    ).toBeVisible();
    await expect(
      page.getByText("summary", { exact: true })
    ).toBeVisible();
    await expect(
      page.getByText("risk_level", { exact: true })
    ).toBeVisible();
  });

  test("contract document preview loads", async ({ page, consoleErrors }) => {
    await page.goto("/module/3");
    await expect(
      page.getByText("Source Document", { exact: false })
    ).toBeVisible();
  });

  test("Behind the Scenes shows CU custom info", async ({ page, consoleErrors }) => {
    await page.goto("/module/3");
    const details = page.locator("details", {
      hasText: "Behind the Scenes",
    });
    await details.locator("summary").click();
    await expect(page.getByText("GPT-4.1 model deployment")).toBeVisible();
  });
});

test.describe("Decision Guide", () => {
  test("page loads", async ({ page, consoleErrors }) => {
    await page.goto("/guide");
    await expect(
      page.getByRole("heading", { name: /Decision Guide/ })
    ).toBeVisible();
  });
});

test.describe("Document API", () => {
  test("list samples returns documents", async ({ request }) => {
    const resp = await request.get("/api/documents/samples");
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.length).toBeGreaterThan(0);
    const names = data.map((d: { name: string }) => d.name);
    expect(names).toContain("invoice.pdf");
    expect(names).toContain("receipt.png");
  });

  test("raw file endpoint serves PNG", async ({ request }) => {
    const resp = await request.get("/api/documents/samples/receipt.png/raw");
    expect(resp.ok()).toBeTruthy();
    expect(resp.headers()["content-type"]).toBe("image/png");
  });

  test("raw file endpoint serves PDF", async ({ request }) => {
    const resp = await request.get("/api/documents/samples/invoice.pdf/raw");
    expect(resp.ok()).toBeTruthy();
    expect(resp.headers()["content-type"]).toBe("application/pdf");
  });

  test("raw file endpoint returns 404 for missing file", async ({
    request,
  }) => {
    const resp = await request.get(
      "/api/documents/samples/nonexistent.xyz/raw"
    );
    expect(resp.status()).toBe(404);
  });
});
