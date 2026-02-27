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
