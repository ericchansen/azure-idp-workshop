import { Route } from "@playwright/test";
import path from "path";
import { test, expect } from "./helpers";

const uploadFixturePath = path.join(process.cwd(), "samples", "invoice.pdf");

function mockJsonRoute(route: Route, body: object, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

function mockTextRoute(route: Route, body: string, status = 500) {
  return route.fulfill({ status, contentType: "text/plain", body });
}

const definitionsResult = {
  result: {
    classifier_analyzer_id: "patient_log_classifier",
    treatment_analyzer_id: "patient_log_treatment",
    definitions: {
      patient_log_classifier: {
        baseAnalyzerId: "prebuilt-document",
        config: {
          enableSegment: true,
          contentCategories: {
            patient_treatment_log: { analyzerId: "patient_log_treatment" },
          },
        },
      },
      patient_log_treatment: {
        baseAnalyzerId: "prebuilt-document",
        fieldSchema: {
          fields: {
            body_diagram_findings: { type: "array" },
            spinal_palpation_findings: { type: "array" },
          },
        },
      },
    },
  },
};

const ensureResult = {
  result: {
    ready: true,
    analyzers: [
      {
        id: "patient_log_treatment",
        kind: "treatment-log extractor",
        status: "ready",
      },
      {
        id: "patient_log_classifier",
        kind: "classifier/segmenter-router",
        status: "ready",
      },
    ],
  },
  trace: {},
};

const analysisResult = {
  result: {
    filename: "patient-log.pdf",
    analyzer_id: "patient_log_classifier",
    analysis: {
      segments: [
        {
          category: "patient_treatment_log",
          pageRange: "pages 1-2",
        },
      ],
      fields: {
        body_diagram_findings: {
          value: [
            {
              region: { valueString: "posterior upper back / scapular area" },
              mark_type: { valueString: "circled region" },
              symptom_interpretation: {
                valueString: "symptom type is unclear from the mark alone",
              },
              confidence: { valueString: "medium" },
            },
          ],
        },
        spinal_palpation_findings: {
          value: [
            {
              level_or_range: { valueString: "C4-C6" },
              mark_description: { valueString: "arrow near cervical spine levels" },
              confidence: { valueString: "medium" },
            },
          ],
        },
      },
      contents: [
        {
          fields: {
            body_diagram_findings: {
              value: [
                {
                  region: { valueString: "posterior upper back / scapular area" },
                  mark_type: { valueString: "circled region" },
                  symptom_interpretation: {
                    valueString: "symptom type is unclear from the mark alone",
                  },
                  confidence: { valueString: "medium" },
                },
              ],
            },
          },
        },
        {
          fields: {
            body_diagram_findings: {
              value: [
                {
                  region: { valueString: "left lower leg / knee region" },
                  mark_type: { valueString: "circled region" },
                  symptom_interpretation: { valueString: "pain mark is possible but unclear" },
                  confidence: { valueString: "medium" },
                },
              ],
            },
            spinal_palpation_findings: {
              value: [
                {
                  level_or_range: { valueString: "C4-C6" },
                  mark_description: { valueString: "arrow near cervical spine levels" },
                  confidence: { valueString: "medium" },
                },
              ],
            },
          },
        },
      ],
    },
  },
  trace: { response_status: 200 },
};

test.describe("Patient Log Analyzer", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/patient-logs/analyzer-definitions", (route) =>
      mockJsonRoute(route, definitionsResult)
    );
  });

  test("loads as a standalone direct page", async ({ page, consoleErrors }) => {
    await page.goto("/patient-log");

    await expect(
      page.getByRole("heading", { name: "Patient Treatment Log Analyzer" })
    ).toBeVisible();
    await expect(page.getByText("CU-only scenario demo")).toBeVisible();
    await expect(page.getByRole("link", { name: /Module 1/i })).not.toBeVisible();
    await expect(page.getByText("patient_log_classifier")).toBeVisible();
  });

  test("creates analyzers and renders analysis findings", async ({ page, consoleErrors }) => {
    await page.route("**/api/patient-logs/ensure-analyzers", (route) =>
      mockJsonRoute(route, ensureResult)
    );
    await page.route("**/api/patient-logs/analyze", (route) =>
      mockJsonRoute(route, analysisResult)
    );

    await page.goto("/patient-log");
    await page.getByLabel("Choose file").setInputFiles(uploadFixturePath);
    await page.getByPlaceholder("Admin key for analyzer setup").fill("test-admin-key");
    await page.getByRole("button", { name: /Create\/update analyzers/i }).click();
    await expect(page.getByText("patient_log_treatment").first()).toBeVisible();

    const analyzeRequestPromise = page.waitForRequest(
      (request) =>
        request.url().endsWith("/api/patient-logs/analyze") && request.method() === "POST"
    );
    await page.getByRole("button", { name: /Analyze packet/i }).click();
    const analyzeRequest = await analyzeRequestPromise;
    expect(analyzeRequest.headers()["content-type"]).toContain("multipart/form-data");

    const findings = page.locator("section").filter({
      has: page.getByRole("heading", { name: "Patient log findings" }),
    });
    await expect(findings.getByText("patient_treatment_log", { exact: true }).first()).toBeVisible();
    await expect(findings.getByText("posterior upper back / scapular area").first()).toBeVisible();
    await expect(findings.getByText("left lower leg / knee region").first()).toBeVisible();
    await expect(findings.getByText("C4-C6").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Export JSON" })).toBeEnabled();
  });

  test("shows plain text API errors without crashing", async ({ page, consoleErrors }) => {
    await page.route("**/api/patient-logs/ensure-analyzers", (route) =>
      mockTextRoute(route, "Service Unavailable", 503)
    );

    await page.goto("/patient-log");
    await page.getByRole("button", { name: /Create\/update analyzers/i }).click();

    await expect(page.getByText("Request failed")).toBeVisible();
    await expect(page.getByText("Service Unavailable")).toBeVisible();
    await expect(page.getByText("Unexpected token")).not.toBeVisible();
  });
});
