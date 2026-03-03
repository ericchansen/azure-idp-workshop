# Hicks — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings
- Module strategy: Module 1 = DI wins at structured, Module 2 = needs rework (currently pointless), Module 3 = CU wins at semantic/unstructured
- **Bishop's Module 1 Proposal**: Restructure as "Structured Extraction — When DI Wins" with prebuilt-invoice scenario, confidence scoring, determinism emphasis. Show DI cost advantage ($0.01/page vs CU $0.05/page).
- **Bishop's Module 2 Proposal**: Replace entire module with "Unstructured-to-Semantic" showing CU advantage on emails, contracts, mixed-format docs. Eliminates redundancy with Module 1.
- **Bishop's Module 3 Proposal**: Enhance with scenario variety (email, research paper, feedback, medical), add token/cost tracking to API trace.
- **Key Teaching Principle**: Show DI and CU on same document in each module. Pedagogical flow: Structured (M1: DI wins) → Semantic (M2: CU wins) → Custom Intelligence (M3: CU's superpower).
- Hicks should be aware Module 1 and 2 restructuring may affect template/test responsibilities.
- **DI confidence architecture**: DI prebuilt models return confidence at two levels — document-level (`documents[].confidence`) and field-level (`documents[].fields.*.confidence`). Both are now surfaced in `_summarize_result` for API trace display.
- **CU token/usage pattern**: CU SDK results may contain `usage` data (promptTokens, completionTokens) either at top level or nested in `contents[]` items. `_result_to_dict` lifts from contents to top level; `_summarize_cu_result` passes it through to API trace.
- **No new endpoints needed**: Existing `/api/di/layout`, `/api/di/prebuilt/{model_id}`, `/api/cu/layout`, `/api/cu/custom` cover all Module 1-3 scenarios including contract extraction (Module 2).
- **Backward-compatible changes only**: All enhancements add optional fields to existing responses — no removals, no structural changes.
- **Multi-revision mode required for PR previews**: ACA label-based URLs (e.g. `---pr-5`) only resolve when `activeRevisionsMode` is `Multiple`. In `Single` mode, the PR revision replaces production and label URLs timeout.
- **Traffic pinning pattern**: When deploying a PR revision in multi-revision mode, always capture the production revision name BEFORE `az containerapp update`, then explicitly set `revision-weight "$PROD_REVISION=100"` after — otherwise the new revision can steal traffic.
- **Prod needs explicit traffic routing too**: In multi-revision mode, `deploy-prod.yml` must explicitly route `latest=100` after Bicep deployment to ensure the new prod revision gets all traffic.
- **Module 3 route removed**: As part of Module 2 + Module 3 consolidation, deleted the `/module/3` route from `server.py` and its corresponding test in `test_pages.py`. API endpoints (`/api/di/layout`, `/api/cu/custom`, etc.) remain unchanged.
