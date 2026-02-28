# Decision: Backend Enhancements for Module Strategy

**By:** Hicks (Backend Dev)
**Date:** 2026-02-28
**Status:** Implemented on `feat/module-strategy-restructure`

## What Changed

1. **DI `_summarize_result`** — Added document-level `confidence` score to API trace summary. Previously only had per-field confidence. Now Lambert can display both document-level and field-level confidence in Module 1 UI.

2. **CU `_result_to_dict`** — Added usage/token data lifting from `contents[]` items to top-level `result.usage`. If CU API returns token counts, they now flow through consistently.

3. **CU `_summarize_cu_result`** — Added `usage` passthrough to API trace summary. Lambert can now display token counts in Module 3's API trace panel.

## What Did NOT Change

- **No new endpoints.** Existing `/api/di/layout`, `/api/di/prebuilt/{model_id}`, `/api/cu/layout`, `/api/cu/custom` support all Module 1-3 scenarios.
- **No breaking changes.** All enhancements add optional fields — backward-compatible with current frontend code.
- **No router changes.** DI and CU routers untouched.

## Impact on Other Agents

- **Lambert**: Can now read `trace.response.body.confidence` (DI doc-level) and `trace.response.body.usage` (CU tokens) in templates.
- **Bishop**: CU token tracking is defensive — works if CU API provides usage data, silently absent if not.
- **Brett**: 4 new unit tests added. E2E tests unaffected (no API contract changes).
