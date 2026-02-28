# Lambert — Module Template Restructure

**Date:** 2025-07-18
**By:** Lambert (Frontend Dev)
**Status:** Implemented on branch `feat/module-strategy-restructure`

## What Changed

Implemented Bishop's module strategy proposal across all templates:

### Module 1 — "Structured Extraction — When DI Wins"
- Headline and subtitle reframed to emphasize DI's strengths
- Teaching point updated: determinism, cost advantage ($0.01 vs $0.05), speed
- Same API endpoints (`/api/di/layout`, `/api/cu/layout`), same Alpine.js logic

### Module 2 — "Unstructured Documents — When DI Falls Short" (FULL REPLACEMENT)
- Old prebuilt model comparison removed entirely
- New module: DI layout vs CU semantic extraction on `contract.txt`
- Uses `/api/di/layout` for DI, `/api/cu/custom` for CU (same endpoints as spec)
- Shows DI returning raw text vs CU returning structured fields (summary, key_parties, obligations, risk_level)
- Alpine.js patterns follow Module 3's established CU custom analysis pattern

### Module 3 — "Custom & Inferred Fields — CU's Unique Power" (ENHANCED)
- Teaching point strengthened: "GenAI-powered semantic extraction on any document type. No predefined fields or training needed."
- Existing functionality preserved — enhancement only

### Index + Base Nav
- Module cards updated with new headlines and subtitles
- Nav links shortened: "Structured", "Unstructured", "Custom Fields"

## Decisions Made
1. **Module 2 reuses Module 3's CU custom pattern** — same fetch to `/api/cu/custom` with JSON body. This creates a pedagogical bridge: Module 2 introduces CU custom fields, Module 3 lets you define your own.
2. **Kept Module 2 document picker simple** — single `contract.txt` button for now. Can add more unstructured doc samples later without template changes.
3. **No Python files modified** — all changes are template/test only as required.

## Impact on Tests
- Unit test `test_module_2_page` updated: asserts "Unstructured" instead of "Prebuilt"
- E2E test assertions were already aligned for "Unstructured" naming
