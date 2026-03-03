# Decision: E2E Test Consolidation for Module 2+3 Merge

**Author:** Vasquez (Tester)
**Date:** 2025-07-19
**Status:** Implemented

## Context

Module 3 ("Custom & Inferred Fields") is being deleted and merged into Module 2. The interactive decision tree wizard on the Decision Guide page is also being removed. All E2E tests referencing these features must be pruned.

## Tests Removed

### Module 3 Tests (across all files)
| File | Block | Tests Cut |
|------|-------|-----------|
| `workshop.spec.ts` | "Module 3 — Custom & Inferred Fields" | 3 |
| `analysis-workflow.spec.ts` | "Module 3 — Analysis Workflow" | 1 |
| `analysis-workflow.spec.ts` | Module 3 error resilience test | 1 |
| `interactions.spec.ts` | "Module 3 — UI Interactions" | 2 |
| `interactions.spec.ts` | "Module 3 — API Trace & Teaching Point" | 3 |
| `interactions.spec.ts` | Module 3 error trace test | 1 |
| `interactions.spec.ts` | Module 3 nav card test + "all cards" assertion | 1 |
| `smoke.spec.ts` | "Smoke: Module 3 — Custom & Inferred Fields" | 1 |
| `smoke.spec.ts` | Behind the Scenes loop (reduced from [1,2,3] to [1,2]) | 1 |
| `teaching-sections.spec.ts` | "Module 3 — Architecture & Setup Section" | 3 |
| `teaching-sections.spec.ts` | "Module 3 — What to Look For & Comparison Guide" | 2 |

### Decision Tree Wizard Tests
| File | Block | Tests Cut |
|------|-------|-----------|
| `interactions.spec.ts` | 6 tree path tests + 1 "Start Over" test | 7 |

**Total removed: ~25 tests**

## Tests Retained

- All Module 1 tests (unchanged)
- All Module 2 tests (unchanged — already test DI layout vs CU custom)
- Decision Guide: comparison matrix table test and scenario cards test (renamed block to "Decision Guide — Static Content")
- All error resilience tests for Modules 1 and 2
- All teaching section tests for Modules 1 and 2
- Homepage nav link assertions updated (3 links: M1, M2, Guide)

## Cleanup

- Removed unused `mockCUCustomErrorWithTrace` fixture from `interactions.spec.ts`
- Updated file header comment in `teaching-sections.spec.ts` ("all 3 modules" → "Modules 1 and 2")

## Why

Module 3 no longer exists as a separate page. Decision tree wizard UI is being replaced with static content. Tests for removed features would fail against the updated app.
