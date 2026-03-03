# Vasquez — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings

### 2026-02-27: Module Strategy E2E Test Updates
- **E2E tests run against the deployed app by default** (`playwright.config.ts` points to Azure Container Apps URL). For testing local template changes, must start `uv run uvicorn workshop.server:app` and set `$env:BASE_URL = "http://127.0.0.1:8000"`.
- **Module 2 flow changed fundamentally**: Was DI prebuilt vs CU prebuilt (invoices/receipts). Now DI layout vs CU custom (contracts). Routes changed from `**/api/di/prebuilt/*` to `**/api/di/layout*` and `**/api/cu/prebuilt/*` to `**/api/cu/custom*`.
- **Playwright `getByRole("heading")` with regex can hit strict mode violations** when multiple headings match (e.g., H1 + H2 both containing "Unstructured"). Fix: use more specific regex like `/Module 2.*Unstructured/`.
- **`getByText()` with broad terms** causes strict violations on Module 2 — "contract" appears in button text, sample name, document content, and teaching points. Use `getByText("contract.txt")` or more specific locators.
- **`waitForAnalysisComplete()` helper** matches "Document Intelligence|Content Understanding" — doesn't work for Module 2's new headings ("DI — Raw Layout Extraction" / "CU — Semantic Extraction"). Module 2 smoke test uses custom wait logic.
- **Module 1 teaching point text changed**: "Both services extract text accurately" → "DI is built for structured, high-volume extraction"
- **Key file paths**: `tests/e2e/workshop.spec.ts` (page load tests), `tests/e2e/analysis-workflow.spec.ts` (mocked analysis + error resilience), `tests/e2e/interactions.spec.ts` (all UI interactions + navigation), `tests/e2e/smoke.spec.ts` (live smoke tests)
- **Test counts**: 60 structural E2E + 12 smoke E2E = 72 total E2E. 51 unit tests.

### 2025-07-18: Teaching Section E2E Tests
- **New file**: `tests/e2e/teaching-sections.spec.ts` — 17 tests covering educational teaching sections across all 3 modules.
- **Teaching sections tested**: Architecture & Setup `<details>` expand/collapse, data flow diagram content, "What Are We Comparing" boxes, Try It Yourself tab switching (Python/cURL), IaC tab switching (Bicep/Terraform/CLI), "What to Look For" amber callout visibility, Comparison Guide sky box appearance after mocked analysis.
- **`getByText()` strict mode with "Browser"** — the word appears in both the diagram element (`<div>Browser</div>`) and a `<p>` paragraph. Fix: use `{ exact: true }` on getByText.
- **Tab content locators**: Use `x-show` attribute selectors like `[x-show="tryTab === 'python'"]` to reliably target Alpine.js tab content panels.
- **Architecture section scoping**: Use `page.locator("details.bg-emerald-50")` to scope all assertions to the Architecture & Setup section, avoiding collisions with other page elements.
- **Pre-existing failures**: 8 existing tests in `interactions.spec.ts` and `analysis-workflow.spec.ts` failing (API Trace visibility issues, `contract.pdf` reference issues). Not caused by new tests.
- **Updated test counts**: 77 structural E2E (60 old + 17 new) + 12 smoke E2E = 89 total E2E. 57 unit tests.

### 2025-07-19: Module 2+3 Consolidation — Test Pruning
- **Module 3 fully removed from all 5 test files**. Module 3 was merged into Module 2; all `/module/3` routes, assertions, and describe blocks deleted.
- **Decision tree wizard tests removed from interactions.spec.ts** (7 tests: 6 tree path tests + 1 "Start Over" test). The interactive decision tree was removed from the Decision Guide page.
- **Kept**: Comparison matrix table test and scenario cards test on Decision Guide — renamed describe block from "Decision Guide — Interactive Tree" to "Decision Guide — Static Content".
- **Removed test blocks**:
  - `workshop.spec.ts`: "Module 3 — Custom & Inferred Fields" (3 tests), Module 3 nav link assertion
  - `analysis-workflow.spec.ts`: "Module 3 — Analysis Workflow" (1 test), Module 3 error resilience test (1 test)
  - `interactions.spec.ts`: "Module 3 — UI Interactions" (2 tests), 7 decision tree tests, "Module 3 — API Trace & Teaching Point" (3 tests), Module 3 error trace test (1 test), Module 3 nav card test (1 test), Module 3 "all cards" assertion
  - `smoke.spec.ts`: "Smoke: Module 3 — Custom & Inferred Fields" (1 test), Module 3 nav link, Behind the Scenes loop reduced from [1,2,3] to [1,2]
  - `teaching-sections.spec.ts`: "Module 3 — Architecture & Setup Section" (3 tests), "Module 3 — What to Look For & Comparison Guide" (2 tests)
- **Total tests removed**: ~25 tests cut. Remaining: ~64 structural E2E + 10 smoke E2E = ~74 total E2E.
- **Unused mock fixture `mockCUCustomErrorWithTrace` cleaned up** from interactions.spec.ts after the only test using it was removed.
