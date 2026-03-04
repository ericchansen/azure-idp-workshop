# Decisions

## Active Decisions

### 2026-02-27T20:56:00Z: Module strategy directive
**By:** Eric Hansen (via Copilot)
**What:** Module 1 should compare and contrast structured extraction — DI should clearly win. Module 2 is pointless and adds nothing new over Module 1 — needs rethinking. Module 3 should showcase scenarios where CU is clearly better than DI.
**Why:** Workshop narrative must tell a clear story: DI wins at structured, CU wins at unstructured/semantic.

---

### 2026-02-27T21:02:00Z: Bishop's Module Strategy Proposal
**By:** Bishop (Azure AI Expert)
**Status:** Ready for Review (Eric Hansen)
**What:** Comprehensive module restructuring proposal addressing the directive above.
- **Module 1**: Restructure as "Structured Extraction — When DI Wins" with prebuilt-invoice scenarios, field-level confidence scoring, cost comparison ($0.01/page DI vs $0.05/page CU). Emphasize determinism and high-volume processing.
- **Module 2**: **Replace entirely** with "Unstructured-to-Semantic — When CU Wins" showing CU's advantage on emails, contracts, mixed-format documents where DI fails. Eliminates redundancy with Module 1.
- **Module 3**: Enhance with scenario variety (email, research paper, customer feedback, medical records), add token count and cost tracking to API trace for transparency.
**Why:** Current modules fail to articulate clear DI vs CU value proposition. Module 1 treats both as interchangeable. Module 2 duplicates Module 1. Module 3 is correct but lacks pedagogy and cost transparency. New structure teaches: Structured (M1: DI wins) → Semantic (M2: CU wins) → Custom Intelligence (M3: CU's superpower).
**Implementation:** No API changes needed. Templates and optional service enhancements. Can proceed incrementally.

---

### 2026-02-27T18:00:00Z: Full Button Coverage E2E Tests
**By:** Brett (Tester)
**Status:** Implemented on branch `test/e2e-coverage-gaps`
**What:** All 16 untested interactive elements (API Trace toggles, CU Formatted/Raw buttons) now covered by E2E tests in `interactions.spec.ts`.
**Why:** Eric's directive: "All button presses on the website must be covered by E2E tests."
**Result:** Structural E2E tests 57 → 72 (all passing). Smoke tests: 12 (unchanged). Total: 84 tests. Every button, toggle, tab, and `<details>` element on site now clicked in at least one test.

---

### 2026-02-27T00:00:00Z: Use `begin_analyze_binary` for CU binary uploads
**By:** Parker (Backend Dev)
**Status:** Applied
**What:** CU service now calls `client.begin_analyze_binary(binary_input=file_bytes)` instead of `begin_analyze()`.
**Why:** `begin_analyze()` hits `:analyze` endpoint (expects JSON). Raw file bytes sent with `content_type="application/octet-stream"` were parsed as empty JSON, causing `ContentEmpty` / `InvalidRequest` errors. `begin_analyze_binary()` hits `:analyzeBinary` endpoint designed for octet-stream uploads.
**Impact:** Fixes CU ContentEmpty errors across all modules (layout, prebuilt, custom). Both `_analyze_prebuilt()` and `analyze_custom()` updated. Trace metadata URLs updated. All unit test mocks updated.
**Rule:** Always use `begin_analyze_binary()` when uploading raw file bytes to CU. The `begin_analyze()` method is for JSON-structured input only.

---

### 2026-02-28T02:51:00Z: CI/CD Deployment Patterns — Add `environment: production` to deploy-prod.yml
**By:** Ripley (DevOps Lead)
**Status:** Decision Ready
**What:** Add single line `environment: production` to `.github/workflows/deploy-prod.yml` deploy job to enable GitHub deployment history visibility and optional approval gates.
**Why:** teamskills repo uses GitHub Environments for deployment tracking and gating. azure-idp-workshop has no Environments defined. Adding `environment: production` makes production deployments visible in GitHub sidebar without changing workflow behavior or adding complexity.
**Scope:** Production only. Do NOT add Environment to `deploy-stage.yml`—PR preview revisions are ephemeral (Container Apps multi-revision mode handles isolation).
**Implementation:** One-line change to `deploy-prod.yml`. Benefits: deployment history visible in GitHub UI, scoped environment secrets capability, optional approval rules. No workflow logic changes, no cost impact.
**Next Steps:** 
1. Update `deploy-prod.yml` with `environment: production`
2. Verify GitHub repo Settings > Environments exists
3. Optional: Add deployment branch protection rule (e.g., require approval for prod, restrict to main)

---

### 2026-02-28T02:51:00Z: Backend Service Enhancements for Module Strategy
**By:** Hicks (Backend Dev)
**Status:** Implemented on `feat/module-strategy-restructure`
**What:** Three backend enhancements to support Bishop's module strategy and Lambert's template work:
1. **DI document-level confidence** — Added `confidence` field to `_summarize_result()` output (existing per-field confidence already present)
2. **CU token usage lifting** — Modified `_result_to_dict()` to extract token counts from `contents[]` items to top-level `result.usage`
3. **CU usage passthrough** — Updated `_summarize_cu_result()` to include `usage` in API trace summary
**Why:** Module 1 now displays document-level DI confidence; Module 3 API trace now shows CU token counts for cost transparency.
**Impact:** No new endpoints. No breaking changes (optional fields, backward-compatible). Lambert templates read `trace.response.body.confidence` (DI) and `trace.response.body.usage` (CU tokens). All 4 new unit tests passing.

---

### 2026-02-28T02:51:00Z: E2E Test Updates for Module Strategy
**By:** Vasquez (Tester)
**Status:** Applied on `feat/module-strategy-restructure`
**What:** All 4 E2E test files updated to match new module strategy:
- `workshop.spec.ts` — Module headings updated for all 3 modules
- `analysis-workflow.spec.ts` — Module 2 routes changed from prebuilt to layout/custom; error resilience adjusted
- `interactions.spec.ts` — Module 2 UI rewritten (Contract doc, Compare button); navigation assertions fixed
- `smoke.spec.ts` — Module 2 smoke rewritten for DI layout vs CU custom flow
**Key Decisions:** 
- Module 2 mock routes: prebuilt → layout/custom
- Button regex: `/Compare|Analyze|Run/i` for flexible matching
- Module 2 smoke uses inline wait on layout/semantic headings (not shared helper)
- Removed "same fields" assertion (Module 2 contrasts raw layout vs semantic)
**Test Results:** 60 structural E2E ✅, 51 unit tests ✅. Smoke tests pending deployment.

---

### 2025-07-18T00:00:00Z: Module Template Restructure — Full Implementation
**By:** Lambert (Frontend Dev)
**Status:** Implemented on `feat/module-strategy-restructure`
**What:** Implemented Bishop's module strategy proposal across all templates:
- **Module 1** — Reframed as "Structured Extraction — When DI Wins"; teaching point emphasizes determinism, cost, speed
- **Module 2** — Completely replaced prebuilt model comparison with DI layout vs CU semantic extraction on contract.txt; uses `/api/di/layout` + `/api/cu/custom`
- **Module 3** — Enhanced teaching point; existing functionality preserved
- Index + nav updated with new headlines and nav shortcuts
**Design Decisions:**
1. Module 2 reuses Module 3's CU custom pattern (pedagogical bridge: M2 introduces CU custom fields, M3 lets you define)
2. Module 2 document picker simple (single contract.txt; can expand later)
3. No Python changes—templates/tests only
**Test Impact:** Unit test `test_module_2_page` updated; E2E assertions aligned.

---

### 2025-07-15T00:00:00Z: Enable Multi-Revision Mode for Container App
**By:** Hicks (Backend Dev)
**Status:** Implemented
**What:** Switched Container App from `activeRevisionsMode: 'Single'` to `'Multiple'` to enable label-based PR preview URL routing.
**Why:** Single-revision mode doesn't support label-based routing; PR URLs (`---pr-N`) were timing out. Multi-revision mode is the only mode supporting ACA label-based revision routing.
**Changes:** 
- Bicep: Added `activeRevisionsMode` parameter, set to `'Multiple'`
- Staging workflow: Added `az containerapp revision set-mode` guard, explicit traffic pinning after PR revision creation
- Prod workflow: Added explicit `latest=100` traffic routing post-Bicep deploy
**Trade-offs:** Pro—PR preview URLs now work, prod traffic protected. Con—old revisions accumulate (deactivation logic handles). Risk—traffic split if `az containerapp ingress traffic set` fails (mitigated with `|| true`).
**Impact:** Affects `infra/modules/container-app.bicep`, `infra/main.bicep`, `deploy-stage.yml`, `deploy-prod.yml`. No Python/template/test impact.

---

### 2026-03-03T20:10:00Z: User Directive — Teaching Depth
**By:** Eric Hansen (via Copilot)
**Status:** Implemented (PR #8)
**What:** Workshop must TEACH people. Each module needs detailed architecture context, optional IaC viewers (Bicep/Terraform/CLI), runnable code examples, and more teaching callouts throughout—not just bottom-of-page "Behind the Scenes."
**Why:** Learners need clear progression: architecture understanding → code execution → infrastructure transparency → cost/performance implications.
**Implementation:** 
- **Module 1**: Pre-demo architecture diagram + Try It Yourself (Python/cURL) + IaC viewers + DI vs CU comparison guide
- **Module 2**: Pre-demo architecture + IaC viewers + teaching callouts + token visibility
- **Module 3**: Pre-demo architecture + IaC viewers + teaching callouts + CLI setup instructions
**Test Results:** 62 E2E + 57 unit = 130 total passing. No regressions.
**Impact:** Templates only (`module1.html`, `module2.html`, `module3.html`). No API/service changes.

---

### 2026-02-24T00:00:00Z: README Documentation Alignment (Post-PR #7)
**By:** Ripley (DevOps Lead)
**Status:** Merged (PR #7)
**What:** Updated README.md module descriptions and tech stack to reflect actual implementation:
- Module 1: "OCR & Layout" → "Structured Extraction — When DI Wins"
- Module 2: "Prebuilt Models" → "Unstructured Documents — When DI Falls Short"  
- Module 3: "Custom Fields" → "Custom & Inferred Fields — CU's Unique Power"
- Tech Stack: Removed HTMX reference (app uses Jinja2 + Alpine.js only)
**Why:** README must match implementation to reduce learner confusion and improve contributor onboarding.
**Implementation:** README.md only; no code/test changes.
**Verification:** Descriptions now match `index.html` and template h1 titles. Tech stack verified against dependencies.

---

### 2026-03-03T22:21Z: User Directive — Consolidate Module 2 and Module 3
**By:** Eric Hansen (via Copilot)
**What:** Module 2 (Unstructured Documents) and Module 3 (Custom Fields) use the same document (contract.pdf), same APIs (`/api/di/layout` + `/api/cu/custom`), same analyzer (`workshopContract`), and nearly identical custom fields. They should be combined into a single module. The only difference is Module 3 adds a `sentiment` field and shows the field definition UI.
**Why:** User observation — the modules are redundant. Same demo, different framing. Should be one module.

---

### 2026-03-03T22:21Z: User Directive — Remove Interactive Decision Tree
**By:** Eric Hansen (via Copilot)
**What:** The interactive decision tree on the Decision Guide page is "silly" — remove it.
**Why:** User preference — the step-by-step wizard doesn't add value.

---

### 2025-02-28T00:00:00Z: Consolidation Plan — Modules 2 & 3 + Decision Guide Refactor
**By:** Ripley (DevOps Lead)
**Status:** PLANNING (no implementation)
**What:** Comprehensive consolidation plan addressing:
1. **Module Consolidation:** Merge Modules 2 and 3 into single "Semantic Extraction & Custom Fields" module (both use contract.pdf, `/api/di/layout` + `/api/cu/custom`, `workshopContract` analyzer)
2. **Decision Guide Refactor:** Remove interactive 4-step decision tree; keep comparison matrix table and scenario cards
3. **Narrative Arc:** Module 1 (DI wins at structured) → Module 2 (CU wins at semantic with custom fields) → Decision Guide (static matrix + scenarios)

**Blast Radius:**
- **Templates:** Delete `module3.html`; merge into `module2.html`; edit `guide.html`, `index.html`, `base.html`
- **Routes:** Delete `module_3()` from `server.py`; add 301 redirect `/module/3` → `/module/2`
- **E2E Tests:** Remove ~25 tests (Module 3 blocks, decision tree tests); update nav assertions to expect 3 links (M1, M2, Guide)
- **APIs:** No changes—`/api/di/layout` and `/api/cu/custom` work for both scenarios

**Work Breakdown:**
- Phase 1 (Vasquez): Test updates and validation
- Phase 2 (Lambert): Template consolidation
- Phase 3 (Hicks): Backend routes
- Phase 4 (Vasquez + Ripley): Final testing and rollout

**Success Criteria:** 70 E2E tests passing (down from 84), smoke tests pass, no console errors, field editing works, 301 redirect functional.

---

### 2025-07-18T00:00:00Z: Lambert — Module Consolidation Implementation
**By:** Lambert (Frontend Dev)
**Status:** Implemented on `feat/module-consolidation`
**What:** Merged Module 3 ("Custom & Inferred Fields") into Module 2, consolidating from 3 modules to 2.
- **Module 2 template:** Now titled "Semantic Extraction & Custom Fields". Added sentiment field (5th field), field definition display UI, merged educational content (IaC includes text-embedding-3-large), updated data flow diagram, teaching points, comparison guide.
- **module3.html:** Deleted.
- **index.html:** Module 3 card removed, grid switched from 4-col to 3-col, Module 2 card updated.
- **base.html:** Module 3 nav link removed, Module 2 nav text updated.
- **guide.html:** Interactive decision tree removed, replaced with static "Choose DI if.../Choose CU if..." summary cards. Comparison matrix and scenario cards preserved.
- **E2E tests:** Heading assertions updated from "Unstructured" to "Semantic" for Module 2.

**Why:** Module 2 and Module 3 were nearly identical—both called `/api/cu/custom` with `workshopContract` analyzer on the same document. The only differences were the sentiment field and field definition display. Consolidation eliminates redundancy and tightens the workshop narrative.

**Impact:** No API/backend changes; E2E tests need re-run against deployed app after merge. Workshop flow is now: Module 1 (DI wins at structured) → Module 2 (CU wins at semantic + custom fields) → Decision Guide.

---

### 2025-07-19T00:00:00Z: E2E Test Consolidation for Module 2+3 Merge
**By:** Vasquez (Tester)
**Status:** Implemented
**What:** Pruned all E2E tests referencing Module 3 and decision tree wizard after consolidation:
- **Module 3 Tests Removed:** 11 tests across workshop.spec.ts, analysis-workflow.spec.ts, interactions.spec.ts, smoke.spec.ts, teaching-sections.spec.ts
- **Decision Tree Wizard Tests Removed:** 7 tree path tests + 1 "Start Over" test
- **Tests Retained:** All Module 1 tests, all Module 2 tests, Decision Guide comparison matrix and scenario cards tests
- **Updates:** Homepage nav link assertions updated (3 links: M1, M2, Guide)
- **Cleanup:** Removed unused `mockCUCustomErrorWithTrace` fixture; updated file header comment

**Total Removed:** ~25 tests

**Why:** Module 3 no longer exists as a separate page; decision tree wizard UI removed. Tests for removed features would fail against updated app.

---

### 2025-07-18T00:00:00Z: Teaching Section E2E Tests in Separate File
**By:** Vasquez (Tester)
**Status:** Implemented on `feat/educational-content`
**What:** Created `tests/e2e/teaching-sections.spec.ts` as a dedicated test file for all educational teaching section coverage (17 tests across 3 modules) rather than adding to `interactions.spec.ts`.

**Why:** 
- `interactions.spec.ts` is already large (694 lines) and covers UI interactions, navigation, error states, and API traces
- Teaching sections are a distinct feature category (Architecture & Setup, Try It Yourself tabs, IaC tabs, What to Look For, Comparison Guide)
- Separation makes it easy to run just teaching section tests: `npx playwright test teaching-sections`
- Follows existing pattern of feature-focused test files

**Impact:** 17 new structural E2E tests added. Total structural E2E: 77 (was 60). Total E2E with smoke: 89. All new tests passing; no changes to existing test files.
