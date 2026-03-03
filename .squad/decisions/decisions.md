# Decisions

## Teaching Section E2E Tests in Separate File
**By:** Vasquez (Tester)  
**Date:** 2025-07-18  
**Status:** Implemented on `feat/educational-content`

### What
Created `tests/e2e/teaching-sections.spec.ts` as a new, separate test file for all educational teaching section coverage (17 tests across 3 modules) rather than adding to `interactions.spec.ts`.

### Why
- `interactions.spec.ts` is already large (694 lines) and covers UI interactions, navigation, error states, and API traces
- Teaching sections are a distinct feature category (Architecture & Setup, Try It Yourself tabs, IaC tabs, What to Look For, Comparison Guide)
- Separation makes it easy to run just teaching section tests: `npx playwright test teaching-sections`
- Follows the existing pattern of feature-focused test files (`workshop.spec.ts`, `analysis-workflow.spec.ts`, `interactions.spec.ts`, `smoke.spec.ts`)

### Impact
- 17 new structural E2E tests added
- Total structural E2E: 77 (was 60)
- Total E2E with smoke: 89
- All new tests passing. No changes to existing test files.

---

## Consolidation Plan: Modules 2 & 3 + Decision Guide Refactor
**Scope:** Analysis of consolidating Modules 2 and 3 into a single module, and removing the interactive decision tree from the Decision Guide.

**Date:** 2025-02-28  
**Lead:** Ripley  
**Status:** PLANNING (no implementation)

### What Stays, What Goes, What Merges

#### Current State
- **Module 2:** "Unstructured Documents — When DI Falls Short" (contract.pdf, `/api/di/layout` vs `/api/cu/custom`)
- **Module 3:** "Custom & Inferred Fields — CU's Unique Power" (contract.pdf, `/api/cu/custom` with field schema UI, includes sentiment field)
- **Decision Guide:** Interactive 4-step decision tree (content type → structure level → existing/new → recommendation) + comparison matrix + scenario cards

#### Key Observation: Redundancy
Both Module 2 and Module 3:
- Use **same document:** `contract.pdf`
- Use **same APIs:** `/api/di/layout` (baseline) + `/api/cu/custom` (analysis)
- Use **same analyzer:** `workshopContract` (renamed from `workshop-custom`)
- Share **nearly identical custom fields:** `summary`, `key_parties`, `obligations`, `risk_level`
- Only difference: Module 3 **adds `sentiment` field** and shows **field definition UI** (user can edit fields)

#### Proposed Consolidation
Create a **single Module 2: "Semantic Extraction & Custom Fields"** that:
1. **Starts with baseline comparison:** DI layout vs CU semantic (no custom fields defined yet)
2. **Progressively teaches field schema:** Shows default custom fields (`summary`, `key_parties`, `obligations`, `risk_level`, `sentiment`)
3. **Lets user customize fields:** Allow field editing (as Module 3 currently does)
4. **Demonstrates field inference:** Re-run analysis with custom fields to show how CU interprets them

**New narrative arc:**
- Module 1 → "DI wins at structured"
- **Module 2 (consolidated)** → "CU wins at semantic understanding with custom fields"
- Module 3 → (promoted to advanced) "Multi-document scenarios & cost/performance optimization"

### Decision Guide Refactor
**Remove:** Interactive decision tree (4-step wizard)  
**Keep:** 
- Comparison Matrix table (feature comparison DI vs CU)
- Scenario Cards (6 common use cases)

**Why:** Tree is educational—works for workshop, not for real-world decision-making. Matrix + scenarios provide faster, more practical guidance.

### Blast Radius Inventory

#### A. Templates to Modify/Delete

| File | Action | Details |
|------|--------|---------|
| `module2.html` | **MERGE INTO** | Keep structure, merge Module 3's field schema UI into it |
| `module3.html` | **DELETE** | All content consolidates into Module 2 |
| `guide.html` | **EDIT** | Remove lines 13–109 (interactive tree). Keep table (112–136) + scenario cards (139–173) |
| `index.html` | **EDIT** | Remove Module 3 card (lines 49–63). Update Module 2 description. Redirect old `/module/3` to `/module/2` or remove nav entirely |
| `base.html` | **EDIT** | Navigation bar: Remove Module 3 link (line 62–65). Update Module 2 nav text |

#### B. Python Routes (server.py + routers)

| File | Action | Details |
|------|--------|---------|
| `server.py` | **EDIT** | Delete `module_3()` route (lines 62–64). Keep `module_2()` intact |
| `di.py` | **NO CHANGE** | `/api/di/layout` works for both old M2 and M3; no modification needed |
| `cu.py` | **NO CHANGE** | `/api/cu/custom` accepts dynamic fields; no modification needed |
| `documents.py` | **CHECK** | Verify `contract.pdf` is only sample needed. If Module 3 used other samples, ensure they're preserved |

**Key insight:** No API changes required. Consolidation is **purely template/UI level.**

#### C. E2E Tests (tests/e2e/)

| File | Refs | Action | Details |
|------|------|--------|---------|
| `workshop.spec.ts` | 14 | **EDIT** | Remove all Module 3 heading/nav assertions (M3 no longer exists). Update nav to expect only M1, M2, Guide |
| `analysis-workflow.spec.ts` | 4 | **EDIT** | Remove Module 3 test block. Module 2 test remains (tests layout vs custom flow) |
| `interactions.spec.ts` | 30 | **EDIT** | Module 2 card test remains. **DELETE** Module 3 card test (line ~1000+). Delete/collapse decision tree tests (lines ~750–850). Keep matrix/scenario card tests |
| `smoke.spec.ts` | 3 | **EDIT** | Module 3 smoke route removed. Module 2 smoke remains |
| `teaching-sections.spec.ts` | 12 | **EDIT** | Remove Module 3 architecture/IaC section tests. Module 2 teaching sections tests remain |
| `helpers.ts` | 0 | **NO CHANGE** | Console error detection works for all modules |

**Smoke test gotcha:** If smoke tests currently expect 3 modules in nav, they will fail. Update nav selectors and counts.

#### D. Educational Content & Teaching Sections

**Currently in Module 2 & Module 3:**
- Architecture & Setup (data flow diagrams, code examples, IaC)
- What Are We Comparing (DI vs CU explanation)
- When to Use in Production (use cases)
- Try It Yourself (Python + cURL examples)
- Infrastructure as Code (Bicep, Terraform, Azure CLI)

**Consolidation approach:**
- **Keep Module 2's architecture** (DI layout vs CU semantic)
- **Integrate Module 3's custom field schema** into Module 2's IaC section (show GPT-4.1 + text-embedding-3-large)
- **Merge "When to Use" sections:** Combine production use cases (contracts, claims, records + custom analysis scenarios)
- **Code examples:** Deduplicate. Module 2 example shows basic custom analyzer; Module 3 example shows sentiment addition. Consolidate into single complete example with all 5 fields

#### E. Infrastructure & Config

| Area | Impact | Details |
|------|--------|---------|
| URLs | **MEDIUM** | `/module/3` route disappears. Update any hardcoded redirects, links in docs, or integration tests. `/guide` remains (but tree removed) |
| Navigation | **LOW** | Update nav bar to show 3 items (M1, M2, Guide) instead of 4 |
| Bookmarks | **EXTERNAL** | Users with bookmarks to `/module/3` will get 404. Recommend 301 redirect from `/module/3` → `/module/2` for grace period, then remove |
| Analytics | **LOW** | Stop tracking `/module/3` page views. Module 2 views will increase (combining both) |

### Success Criteria

✅ All 70 E2E tests pass (down from 84)  
✅ All 51 unit tests pass  
✅ **Smoke tests pass on staging** (live `/module/2` and `/guide` work)  
✅ No console errors in Module 2 or Decision Guide  
✅ Navigation bar renders correctly with 3 items (M1, M2, Guide)  
✅ `/module/3` returns 301 redirect to `/module/2`  
✅ No broken links in index.html or base.html  
✅ Field editing in consolidated Module 2 works (add/remove fields, re-run analysis)  
✅ Decision Guide matrix and scenario cards display correctly without tree  

### Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-02-28 | Consolidate M2 & M3 | Remove redundancy (same doc, APIs, analyzer); simplify narrative |
| 2025-02-28 | Remove decision tree | Interactive tree doesn't align with hands-on workshop pedagogy; matrix + scenarios sufficient |
| 2025-02-28 | Keep 301 redirect for 90 days | Grace period for external links; prevents immediate 404 breakage |
| 2025-02-28 | No API changes | `/api/di/layout` and `/api/cu/custom` support both old M2 and M3 use cases |

---

## No 301 Redirect Needed for /module/3
**By:** Eric Hansen  
**Date:** 2026-03-03  
**Status:** APPROVED

### What
Remove `/module/3` route entirely without setting up a 301 redirect to `/module/2`. The demo app does not need to preserve bookmarks or external links.

### Why
This is a demo application. External SEO and bookmark preservation are not concerns. Simplifies the consolidation by avoiding redirect routing logic.

### Decision
Skip the 301 redirect implementation. Just delete the `module_3()` route from `server.py`.
