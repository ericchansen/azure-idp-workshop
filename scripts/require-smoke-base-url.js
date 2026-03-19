"use strict";

const baseUrl = process.env.BASE_URL;

if (!baseUrl) {
  console.error(
    'Smoke tests require BASE_URL to point to a deployed app. Example: BASE_URL=https://your-app.azurecontainerapps.io npx playwright test --grep Smoke --project="Desktop Edge"'
  );
  process.exit(1);
}

let parsedUrl;
try {
  parsedUrl = new URL(baseUrl);
} catch {
  console.error(`Smoke tests require a valid BASE_URL, got: ${baseUrl}`);
  process.exit(1);
}

if (["localhost", "127.0.0.1", "::1"].includes(parsedUrl.hostname)) {
  console.error(
    `Smoke tests must target a deployed app, not ${baseUrl}. Use --grep-invert Smoke for local structural testing.`
  );
  process.exit(1);
}
