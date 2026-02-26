import { defineConfig } from "@playwright/test";

const BASE_URL =
  process.env.BASE_URL ||
  "https://idp-workshop.yellowbush-cb9b34cb.eastus.azurecontainerapps.io";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: 1,
  reporter: "html",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "Desktop Edge",
      use: { channel: "msedge" },
    },
  ],
});
