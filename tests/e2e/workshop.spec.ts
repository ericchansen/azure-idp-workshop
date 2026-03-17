import { test, expect } from "./helpers";

test.describe("API Contracts", () => {
  test("health endpoint returns ok", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });

  test("list samplesreturns documents", async ({ request }) => {
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
