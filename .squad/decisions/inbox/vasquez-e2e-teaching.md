# Decision: Teaching Section E2E Tests in Separate File

**By:** Vasquez (Tester)
**Date:** 2025-07-18
**Status:** Implemented on `feat/educational-content`

## What
Created `tests/e2e/teaching-sections.spec.ts` as a new, separate test file for all educational teaching section coverage (17 tests across 3 modules) rather than adding to `interactions.spec.ts`.

## Why
- `interactions.spec.ts` is already large (694 lines) and covers UI interactions, navigation, error states, and API traces
- Teaching sections are a distinct feature category (Architecture & Setup, Try It Yourself tabs, IaC tabs, What to Look For, Comparison Guide)
- Separation makes it easy to run just teaching section tests: `npx playwright test teaching-sections`
- Follows the existing pattern of feature-focused test files (`workshop.spec.ts`, `analysis-workflow.spec.ts`, `interactions.spec.ts`, `smoke.spec.ts`)

## Impact
- 17 new structural E2E tests added
- Total structural E2E: 77 (was 60)
- Total E2E with smoke: 89
- All new tests passing. No changes to existing test files.
