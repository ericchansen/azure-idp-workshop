# Consolidation Plan: Modules 2 & 3 + Decision Guide Refactor

**Scope:** Analysis of consolidating Modules 2 and 3 into a single module, and removing the interactive decision tree from the Decision Guide.

**Date:** 2025-02-28  
**Lead:** Ripley  
**Status:** PLANNING (no implementation)

---

## 1. What Stays, What Goes, What Merges

### Current State
- **Module 2:** "Unstructured Documents — When DI Falls Short" (contract.pdf, `/api/di/layout` vs `/api/cu/custom`)
- **Module 3:** "Custom & Inferred Fields — CU's Unique Power" (contract.pdf, `/api/cu/custom` with field schema UI, includes sentiment field)
- **Decision Guide:** Interactive 4-step decision tree (content type → structure level → existing/new → recommendation) + comparison matrix + scenario cards

### Key Observation: Redundancy
Both Module 2 and Module 3:
- Use **same document:** `contract.pdf`
- Use **same APIs:** `/api/di/layout` (baseline) + `/api/cu/custom` (analysis)
- Use **same analyzer:** `workshopContract` (renamed from `workshop-custom`)
- Share **nearly identical custom fields:** `summary`, `key_parties`, `obligations`, `risk_level`
- Only difference: Module 3 **adds `sentiment` field** and shows **field definition UI** (user can edit fields)

### Proposed Consolidation
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

---

## 2. Blast Radius Inventory

### A. Templates to Modify/Delete

| File | Action | Details |
|------|--------|---------|
| `module2.html` | **MERGE INTO** | Keep structure, merge Module 3's field schema UI into it |
| `module3.html` | **DELETE** | All content consolidates into Module 2 |
| `guide.html` | **EDIT** | Remove lines 13–109 (interactive tree). Keep table (112–136) + scenario cards (139–173) |
| `index.html` | **EDIT** | Remove Module 3 card (lines 49–63). Update Module 2 description. Redirect old `/module/3` to `/module/2` or remove nav entirely |
| `base.html` | **EDIT** | Navigation bar: Remove Module 3 link (line 62–65). Update Module 2 nav text |

### B. Python Routes (server.py + routers)

| File | Action | Details |
|------|--------|---------|
| `server.py` | **EDIT** | Delete `module_3()` route (lines 62–64). Keep `module_2()` intact |
| `di.py` | **NO CHANGE** | `/api/di/layout` works for both old M2 and M3; no modification needed |
| `cu.py` | **NO CHANGE** | `/api/cu/custom` accepts dynamic fields; no modification needed |
| `documents.py` | **CHECK** | Verify `contract.pdf` is only sample needed. If Module 3 used other samples, ensure they're preserved |

**Key insight:** No API changes required. Consolidation is **purely template/UI level.**

### C. E2E Tests (tests/e2e/)

| File | Refs | Action | Details |
|------|------|--------|---------|
| `workshop.spec.ts` | 14 | **EDIT** | Remove all Module 3 heading/nav assertions (M3 no longer exists). Update nav to expect only M1, M2, Guide |
| `analysis-workflow.spec.ts` | 4 | **EDIT** | Remove Module 3 test block. Module 2 test remains (tests layout vs custom flow) |
| `interactions.spec.ts` | 30 | **EDIT** | Module 2 card test remains. **DELETE** Module 3 card test (line ~1000+). Delete/collapse decision tree tests (lines ~750–850). Keep matrix/scenario card tests |
| `smoke.spec.ts` | 3 | **EDIT** | Module 3 smoke route removed. Module 2 smoke remains |
| `teaching-sections.spec.ts` | 12 | **EDIT** | Remove Module 3 architecture/IaC section tests. Module 2 teaching sections tests remain |
| `helpers.ts` | 0 | **NO CHANGE** | Console error detection works for all modules |

**Smoke test gotcha:** If smoke tests currently expect 3 modules in nav, they will fail. Update nav selectors and counts.

### D. Educational Content & Teaching Sections

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

### E. Infrastructure & Config

| Area | Impact | Details |
|------|--------|---------|
| URLs | **MEDIUM** | `/module/3` route disappears. Update any hardcoded redirects, links in docs, or integration tests. `/guide` remains (but tree removed) |
| Navigation | **LOW** | Update nav bar to show 3 items (M1, M2, Guide) instead of 4 |
| Bookmarks | **EXTERNAL** | Users with bookmarks to `/module/3` will get 404. Recommend 301 redirect from `/module/3` → `/module/2` for grace period, then remove |
| Analytics | **LOW** | Stop tracking `/module/3` page views. Module 2 views will increase (combining both) |

---

## 3. Decision Guide: What Replaces the Interactive Tree?

### Current Structure (lines 14–109)
```
Interactive Decision Tree (4 steps)
├─ Step 1: Content type (documents, audio, images)
├─ Step 2: Structure level (highly, semi, unstructured)
├─ Step 3: New/existing DI deployment
└─ Step 4: Recommendation (CU, DI, or hybrid)
```

### Issues with Tree
1. **Not pedagogical for workshop:** Doesn't teach _why_ one service is better; just routes to answer
2. **Too prescriptive:** Real decisions require nuance (cost, latency, model maturity) not covered
3. **Redundant after modules:** Workshop already teaches DI vs CU through hands-on examples
4. **Misleading "new project" → CU:** Older deployments may prefer DI stability over CU beta

### Proposed Replacement

**Keep:** 
- **Comparison Matrix table** (lines 112–136)  
  Shows feature parity: OCR, prebuilt models, custom fields, multimodal, GenAI, latency, cost, SDK maturity, recommendations
  
- **Scenario Cards** (lines 139–173)  
  6 concrete examples: contracts (CU), vendor invoices (CU), tax forms (DI/CU), calls (CU), research (CU), IDs (DI/CU)

**Add (optional):**
- **Concise written decision logic** above the matrix:
  ```
  Choose DI if: 
  - High-volume structured forms (invoices, receipts, IDs)
  - Need deterministic, cost-optimized processing
  - Already deployed DI in production
  
  Choose CU if:
  - Extracting meaning from varied/unstructured docs
  - Need GenAI field inference without training
  - Working with audio, video, or images
  ```

**Rationale:** This mirrors the real user journey: 
1. Read scenario cards → find your use case
2. Check matrix → verify feature support
3. Quick reference logic → decide

---

## 4. Risks and Gotchas

### 🔴 High Risk
1. **Smoke test failure on deployment:** If live tests expect 3 nav links and only 2 exist, smoke tests fail. **Mitigation:** Update nav selectors before consolidation; run smoke tests locally.
2. **Lost module progression:** Users expecting 3 separate modules may be confused by "Module 2" doing both M2+M3 work. **Mitigation:** Explicitly document in module2.html that it covers both semantic extraction AND custom field definition.

### 🟡 Medium Risk
3. **External links to `/module/3`:** README, external docs, blog posts, YouTube tutorials may reference `/module/3`. **Mitigation:** Add 301 redirect in FastAPI (`@app.get("/module/3")` → redirect to `/module/2`); can remove after 6 months.
4. **Field schema conflicts:** If Module 3 ever adds a 6th field beyond sentiment, Module 2 (only 5 fields) would be incomplete. **Mitigation:** Document consolidated field set; if future fields added, update once in consolidated module.
5. **Navigation bar width:** With Module 3 removed, nav shrinks. Some CSS may break if grid assumes 4 items. **Mitigation:** Review `base.html` nav CSS; test responsive design.

### 🟢 Low Risk
6. **API test mocks:** Unit tests mock `/api/di/layout` and `/api/cu/custom`. Both still work; no mock changes needed.
7. **Document samples:** Both modules use `contract.pdf`; no new samples to manage.
8. **Analyzer ID:** Both use `workshopContract`; no change.

### URL Redirect Strategy
```python
# In server.py
@app.get("/module/3", response_class=RedirectResponse)
async def redirect_module_3():
    return RedirectResponse(url="/module/2", status_code=301)
```
Keep for 2–3 months, then remove.

---

## 5. Suggested Work Breakdown

### Phase 1: Planning & Test Updates (Vasquez)
**Who:** Vasquez (Tester)  
**Duration:** 1 session  
**Tasks:**
1. ✅ Review all E2E test references to `/module/3` (found 14 in workshop.spec.ts, 4 in analysis-workflow.spec.ts, etc.)
2. Update E2E test files:
   - `workshop.spec.ts` — Remove Module 3 nav/heading assertions
   - `analysis-workflow.spec.ts` — Remove Module 3 test block
   - `interactions.spec.ts` — Remove Module 3 card test, decision tree tests
   - `smoke.spec.ts` — Update nav link count to 3
   - `teaching-sections.spec.ts` — Remove Module 3 section tests
3. Run tests locally to verify they pass with new expectations (before implementation)
4. Document test count change (currently ~84 tests → ~70 after consolidation)

### Phase 2: Template Consolidation (Lambert)
**Who:** Lambert (Frontend Dev)  
**Duration:** 1–2 sessions  
**Tasks:**
1. **Merge Module 3 into Module 2:**
   - Copy Module 3's field schema UI (Alpine.js) to Module 2
   - Integrate field definition inputs with analysis flow
   - Merge "When to Use" and "Try It Yourself" sections
   - Consolidate IaC examples (keep both GPT-4.1 & embedding references)
2. **Delete `module3.html`**
3. **Edit `guide.html`:**
   - Remove decision tree (lines 13–109)
   - Add 3–4 line written decision logic above matrix (optional)
4. **Edit `index.html`:**
   - Remove Module 3 card
   - Update Module 2 card description: "Semantic Extraction & Custom Fields — CU's Superpower"
   - Update badges: "CU Wins", "Semantic + GenAI"
5. **Edit `base.html`:**
   - Remove Module 3 nav link
   - Test responsive design (nav now has 3 items)
6. **Run Playwright structural E2E tests** locally to catch any UI regressions

### Phase 3: Backend Routes (Hicks)
**Who:** Hicks (Backend Dev)  
**Duration:** 0.5 session  
**Tasks:**
1. Delete `module_3()` route from `server.py`
2. Add 301 redirect route: `/module/3` → `/module/2` (keep for 90 days)
3. Run unit tests to confirm no breakage
4. Verify `/api/di/layout` and `/api/cu/custom` still work (no changes needed)

### Phase 4: Final Testing & Rollout (Vasquez + Ripley)
**Who:** Vasquez (Tester), Ripley (Gate)  
**Duration:** 1 session  
**Tasks:**
1. Run full test suite locally (all 70 updated E2E tests + unit tests)
2. **Run smoke tests against staging deployment** to confirm live module 2/guide work
3. Code review gate (Ripley) on PR
4. Merge to main
5. Monitor prod deployment for 404 errors on `/module/3`
6. Document decision in `.squad/decisions.md`

---

## 6. Implementation Notes for Each Agent

### For Vasquez (Tester)
- Interacting with two files to delete/edit shouldn't require mocks; you're removing test cases
- Be aggressive with removing Module 3 tests—this is intentional de-duplication, not a loss
- Watch for navigation bar tests that count items; update counts accordingly

### For Lambert (Frontend Dev)
- **Alpine.js data merging:** Module 2 has `diResult`, `cuResult`, `fields`, `startAnalysis()`. Module 3 has `cuResult`, `diResult`, `fields` (5 instead of 4). Merge carefully; ensure state management doesn't conflict.
- **Field persistence:** When user edits fields and re-runs analysis, ensure Module 2 remembers edits across runs (as M3 currently does)
- **Teaching narrative:** Update Module 2's intro paragraph to explain it covers both DI vs CU AND custom field definition

### For Hicks (Backend Dev)
- No service code changes; purely routes
- The 301 redirect is temporary; document that it should be removed in 90 days (add TODO)
- Verify analyzer name `workshopContract` is consistent between DI and CU routes

### For Ripley (Architect/Lead)
- **Decision Gate:** Approve consolidation in `.squad/decisions.md` once work is done
- **Narrative:** Ensure new Module 2 story is clear: "See DI extract text, CU extract meaning, then customize CU's fields"
- **Docs:** Update README if it mentions Module 3

---

## 7. Files Summary

### **DELETE**
- `src/workshop/templates/module3.html` (entire file)

### **EDIT**
- `src/workshop/templates/module2.html` — Merge M3 content, update Alpine.js data
- `src/workshop/templates/guide.html` — Remove decision tree (150 lines)
- `src/workshop/templates/index.html` — Remove M3 card, update M2 description
- `src/workshop/templates/base.html` — Remove M3 nav link
- `src/workshop/server.py` — Delete module_3() route, add 301 redirect
- `tests/e2e/workshop.spec.ts` — Remove M3 nav/heading tests
- `tests/e2e/analysis-workflow.spec.ts` — Remove M3 test block
- `tests/e2e/interactions.spec.ts` — Remove M3 card & decision tree tests
- `tests/e2e/smoke.spec.ts` — Remove M3 route test, update nav count
- `tests/e2e/teaching-sections.spec.ts` — Remove M3 section tests

### **NO CHANGE**
- `src/workshop/routers/di.py` — API works as-is
- `src/workshop/routers/cu.py` — API works as-is
- `src/workshop/routers/documents.py` — contract.pdf only document needed
- All unit tests — Mocks work for both old M2+M3 scenarios

---

## 8. Success Criteria

✅ All 70 E2E tests pass (down from 84)  
✅ All 51 unit tests pass  
✅ **Smoke tests pass on staging** (live `/module/2` and `/guide` work)  
✅ No console errors in Module 2 or Decision Guide  
✅ Navigation bar renders correctly with 3 items (M1, M2, Guide)  
✅ `/module/3` returns 301 redirect to `/module/2`  
✅ No broken links in index.html or base.html  
✅ Field editing in consolidated Module 2 works (add/remove fields, re-run analysis)  
✅ Decision Guide matrix and scenario cards display correctly without tree  

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-02-28 | Consolidate M2 & M3 | Remove redundancy (same doc, APIs, analyzer); simplify narrative |
| 2025-02-28 | Remove decision tree | Interactive tree doesn't align with hands-on workshop pedagogy; matrix + scenarios sufficient |
| 2025-02-28 | Keep 301 redirect for 90 days | Grace period for external links; prevents immediate 404 breakage |
| 2025-02-28 | No API changes | `/api/di/layout` and `/api/cu/custom` support both old M2 and M3 use cases |
