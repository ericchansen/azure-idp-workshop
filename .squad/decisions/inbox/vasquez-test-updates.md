# Decision: E2E Tests Updated for Module Strategy

**By:** Vasquez (Tester)
**Date:** 2026-02-27
**Status:** Applied on branch `feat/module-strategy-restructure`

## What Changed

All 4 E2E test files updated to match the new module strategy:

| File | Changes |
|------|---------|
| `workshop.spec.ts` | Heading regexes updated for all 3 modules |
| `analysis-workflow.spec.ts` | Module 2 routes changed from prebuilt to layout/custom, error resilience updated |
| `interactions.spec.ts` | Module 2 UI tests rewritten (Contract doc, Compare button), navigation heading assertions fixed, teaching point text updated |
| `smoke.spec.ts` | Module 2 smoke rewritten for DI layout vs CU custom flow, custom wait logic (not `waitForAnalysisComplete`) |

## Key Decisions

1. **Module 2 mock routes**: Changed from `**/api/di/prebuilt/*` + `**/api/cu/prebuilt/*` to `**/api/di/layout*` + `**/api/cu/custom*` to match Lambert's new template JS.
2. **Button regex**: Used `/Compare|Analyze|Run/i` to flexibly match the new "Compare DI Layout vs CU Semantic" button text.
3. **Module 2 smoke wait**: Cannot use shared `waitForAnalysisComplete()` because Module 2 headings are "DI — Raw Layout Extraction" / "CU — Semantic Extraction", not "Document Intelligence" / "Content Understanding". Used inline wait on `/DI — Raw Layout|CU — Semantic/`.
4. **Removed "Both services extract the same fields" assertion**: Module 2's teaching point no longer compares identical field extraction — it contrasts raw layout vs semantic understanding.

## Test Results

- 60 structural E2E: ✅ all passing (against local server with updated templates)
- 51 unit tests: ✅ all passing
- Smoke tests: Not yet runnable (deployed app still has old templates)

## Note for Lambert

Smoke tests will fail until the new templates are deployed. After deployment, run:
```bash
npx playwright test --grep Smoke --project="Desktop Edge"
```
