# Lambert — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings
- Module strategy: Module 1 = DI wins at structured, Module 2 = needs rework (currently pointless), Module 3 = CU wins at semantic/unstructured
- **Bishop's Module 1 Proposal**: Restructure as "Structured Extraction — When DI Wins" with prebuilt-invoice scenario, confidence scoring, determinism emphasis. Show DI cost advantage ($0.01/page vs CU $0.05/page).
- **Bishop's Module 2 Proposal**: Replace entire module with "Unstructured-to-Semantic" showing CU advantage on emails, contracts, mixed-format docs. Eliminates redundancy with Module 1.
- **Bishop's Module 3 Proposal**: Enhance with scenario variety (email, research paper, feedback, medical), add token/cost tracking to API trace.
- **Key Teaching Principle**: Show DI and CU on same document in each module. Pedagogical flow: Structured (M1: DI wins) → Semantic (M2: CU wins) → Custom Intelligence (M3: CU's superpower).
- Lambert should be aware Module 3 enhancement (token/cost tracking) may affect service layer responsibilities.
- **Module Restructure Implemented (2025-07-18)**: All templates restructured per Bishop's proposal:
  - Module 1: headline/subtitle/teaching point reframed for DI advantage. Same `/api/di/layout` + `/api/cu/layout` endpoints, same Alpine.js logic.
  - Module 2: **Fully replaced** — old prebuilt comparison removed. New module uses `/api/di/layout` + `/api/cu/custom` on `contract.txt`, showing DI's text-only output vs CU's semantic field extraction (summary, key_parties, obligations, risk_level). Same Alpine.js patterns as Module 3.
  - Module 3: Teaching point enhanced to emphasize "CU's superpower" and "no predefined fields or training needed." Existing functionality untouched.
  - Index cards, base.html nav labels updated to match.
  - Unit test `test_module_2_page` updated: asserts "Unstructured" instead of "Prebuilt".
- **Pattern**: Module 2 now shares the same CU custom analysis pattern as Module 3 (POST to `/api/cu/custom` with JSON body containing `sample`, `fields`, `analyzer_id`).
- **E2E test expectations** were already pre-aligned for "Unstructured" naming in existing test files.
- **Module Consolidation (2025-07-18)**: Merged Module 3 into Module 2, deleted module3.html.
  - Module 2 title: "Semantic Extraction & Custom Fields" (was "Unstructured Documents — When DI Falls Short")
  - Added `sentiment` field to Alpine.js `fields` array (5 fields total: summary, key_parties, obligations, risk_level, sentiment)
  - Added Custom Field Definitions display UI with name/description/type badges (from Module 3)
  - Merged educational content: data flow diagram now shows full GPT-4.1 → Structured Fields pipeline, IaC includes text-embedding-3-large in all 3 tabs, production use cases merged
  - Button text: "🧠 Run CU Custom + DI Layout" (from Module 3)
  - Teaching point merged: combines "DI Falls Short" + "CU's Superpower" messaging
  - Comparison guide: GenAI vs Deterministic, Schema-Driven No Training, Cost vs Value
  - Removed "Next: Module 3" forward reference from teaching point
  - index.html: Module 3 card removed, grid changed from 4-col to 3-col, Module 2 card updated
  - base.html: Module 3 nav link removed, Module 2 nav text changed to "Semantic & Custom"
  - guide.html: Decision tree wizard removed, replaced with "Choose DI if.../Choose CU if..." summary cards
  - E2E test heading assertions updated: `/Module 2.*Unstructured/` → `/Module 2.*Semantic/`
  - API endpoints unchanged: `/api/di/layout` + `/api/cu/custom` with `workshopContract` analyzer
