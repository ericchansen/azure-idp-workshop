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
