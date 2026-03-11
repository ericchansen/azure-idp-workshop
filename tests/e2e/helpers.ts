import { test as base, expect, type Page, type ConsoleMessage } from "@playwright/test";

/**
 * Known warnings/errors that should not fail tests.
 * These are browser-level messages, not application-level errors.
 */
const ALLOWED_PATTERNS: RegExp[] = [
  /Download the Vue Devtools/i,
  /Alpine\.js/i,
  /DevTools/i,
  /Autofocus processing was blocked/i,
  /third-party cookie/i,
  // Browser network errors from mocked/failed API responses
  /Failed to load resource/i,
  // Favicon and other non-critical resource loads
  /favicon\.ico/i,
];

function isAllowed(text: string): boolean {
  return ALLOWED_PATTERNS.some((p) => p.test(text));
}

/**
 * Extended test fixture that captures console errors during each test.
 * Any unexpected console.error messages cause the test to fail.
 */
export const test = base.extend<{ consoleErrors: string[] }>({
  consoleErrors: async ({ page }, use) => {
    const errors: string[] = [];

    page.on("console", (msg: ConsoleMessage) => {
      if (msg.type() === "error" && !isAllowed(msg.text())) {
        errors.push(msg.text());
      }
    });

    page.on("pageerror", (err) => {
      errors.push(`Page error: ${err.message}`);
    });

    await use(errors);

    if (errors.length > 0) {
      throw new Error(
        `Unexpected console errors during test:\n${errors.map((e) => `  • ${e}`).join("\n")}`
      );
    }
  },
});

export { expect };

/**
 * Assert that no error banners are visible on the page.
 * Call this after any analysis workflow completes.
 */
export async function assertNoErrorBanners(page: Page): Promise<void> {
  // These texts should NEVER appear after a successful analysis
  const forbidden = [
    "Analysis Failed",
    "Indexing Failed",
    "Search Failed",
    "Internal Server Error",
    "Unexpected token",
    "Service Unavailable",
    "Gateway Timeout",
    "502 Bad Gateway",
  ];

  for (const text of forbidden) {
    await expect(page.getByText(text).first()).not.toBeVisible({ timeout: 2000 });
  }
}

/**
 * Wait for analysis to complete (loading spinners gone, results visible).
 */
export async function waitForAnalysisComplete(page: Page): Promise<void> {
  // Wait for at least one result heading to appear.
  // Use " — " (em dash) to match result headings like "Document Intelligence — Layout"
  // and NOT the hidden Architecture section headers like "Document Intelligence (DI)".
  await expect(
    page
      .getByText(
        /Document Intelligence —|Content Understanding —|DI —|CU —|Analysis Unavailable/
      )
      .first()
  ).toBeVisible({ timeout: 120_000 });

  // Wait for ALL loading indicators to disappear (not just the first)
  // This ensures both DI and CU have finished, even if one is slower
  await expect(page.locator(".animate-pulse")).toHaveCount(0, { timeout: 120_000 });
}
