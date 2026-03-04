# Bishop — History

## Project Context
Azure IDP Workshop — interactive demo comparing Azure Document Intelligence (DI) and Azure Content Understanding (CU). FastAPI + Alpine.js + Tailwind CSS. Python 3.12 with uv. Deployed to Azure Container Apps. User: Eric Hansen.

## Learnings
- Module strategy directive from Eric: Module 1 = DI wins at structured extraction, Module 2 = needs rework (currently pointless), Module 3 = CU wins at semantic/unstructured understanding
- **Module 1 Issue**: Currently positions OCR/layout as "both services do this equally well." Should pivot to "Structured Extraction — DI's Strength" with prebuilt-invoice scenario, confidence scoring, and determinism emphasis.
- **Module 2 Issue**: Functionally identical to Module 1 (both run prebuilt models on same document). **Solution**: Replace entirely with "Unstructured-to-Semantic" module showing CU's advantage for emails, contracts, mixed-format docs where DI fails.
- **Module 3 Success**: Correctly showcases CU's GenAI superpower. Recommendations: add scenario variety (email, research paper, feedback), enhance token/cost tracking in API trace.
- **DI Win Condition**: Structured forms, predefined fields, high-volume processing, deterministic extraction. Confidence scoring is key differentiator.
- **CU Win Condition**: Unstructured/semantic extraction, novel document types, GenAI inference needed for meaning.
- **Leverage Opportunities**: Confidence scoring visibility (Module 1), markdown output (Module 2), token cost tracking (Module 3), table detection (Module 1).
- **Teaching Principle**: Show DI and CU on same document in each module. Comparison clarifies value proposition. Pedagogical flow: Structured (M1) → Semantic (M2) → Custom Intelligence (M3).

## 2025-02-28 CU Production Failure Investigation

**Context**: 3/9 smoke tests failing in production — all CU-related (Module 2 contract analysis). DI tests pass. Production app deployed to Azure Container Apps.

**Root Cause — Model Deployment Name Mismatch**:
The CU service hardcodes model reference as `"gpt-4.1"` in two critical places:
1. `_ensure_defaults()` — maps `"gpt-4.1": settings.cu_completion_deployment` (line 146)
2. `_ensure_analyzer()` — sets `"models": {"completion": "gpt-4.1"}` (line 168)

**The Problem**:
- Bicep deploys model as `name: 'gpt-41'` (no dot) in `ai-services.bicep` line 29
- CU SDK expects `"gpt-4.1"` (with dot) as model identifier
- Config default `cu_completion_deployment: str = "gpt-41"` matches Bicep but NOT SDK usage
- **Mismatch**: SDK asks for `"gpt-4.1"` → config points to deployment `"gpt-41"` → Azure API fails to find model

**Why DI Works**:
DI uses `prebuilt-layout` analyzers that don't require custom model deployments. DI just needs Cognitive Services endpoint + credentials.

**Why CU Fails**:
1. `analyze_layout()` and `analyze_prebuilt()` use prebuilt CU analyzers → may work (need verification)
2. **`analyze_custom()` ALWAYS fails** because:
   - Calls `_ensure_analyzer()` which creates analyzer with `"completion": "gpt-4.1"`
   - CU SDK attempts to find deployed model named `"gpt-4.1"`
   - Azure AI Services only has deployment named `"gpt-41"`
   - Azure returns error (likely 404 or InvalidRequest for missing model)

**Evidence**:
- Module 2 smoke test fails on CU custom analysis (contract scenario uses `/api/cu/custom`)
- Test waits 120s for CU spinner to disappear (timeout suggests long retry/failure loop)
- Console errors fixture would catch JS errors if API returned 500/error banner

**Failure Modes**:
1. **Silent failure in `update_defaults()`** — Line 153 catches exception, logs warning, continues. If defaults fail to set, subsequent analyzer creation may still proceed but use wrong/missing model.
2. **Analyzer creation failure** — `_ensure_analyzer()` creates analyzer with model ref `"gpt-4.1"` but deployment doesn't exist. SDK may accept creation but fail on first analysis attempt.
3. **Analysis-time failure** — When `begin_analyze_binary()` runs, CU backend tries to invoke completion model `"gpt-4.1"`, fails to find deployment, returns HttpResponseError.

**Fix Options**:

**Option A: Change Bicep deployment name to match SDK** (RECOMMENDED)
- Change `infra/modules/ai-services.bicep` line 29: `name: 'gpt-41'` → `name: 'gpt-4.1'`
- Pro: SDK code stays clean, follows Azure naming conventions for model versions
- Con: Requires infra redeployment, may break if Azure rejects dots in deployment names (needs testing)

**Option B: Change code to match Bicep deployment name**
- Change `content_understanding.py` line 146: `"gpt-4.1"` → `"gpt-41"`
- Change `content_understanding.py` line 168: `"gpt-4.1"` → `"gpt-41"`
- Pro: No infra change needed, can deploy immediately
- Con: Hardcoded string in two places (DRY violation), model identifier doesn't match actual model version

**Option C: Make model identifier configurable**
- Add `settings.cu_completion_model_id: str = "gpt-4.1"` to config
- Use `settings.cu_completion_model_id` in both `update_defaults()` and `_ensure_analyzer()`
- Change Bicep deployment name to `gpt-4.1` OR change config default to `"gpt-41"`
- Pro: Decouples model identifier from deployment name, most flexible
- Con: Adds complexity, another config variable to document

**Recommendation**: **Option A** — Change Bicep to `name: 'gpt-4.1'` to match SDK expectations. Model version identifiers should include dots for clarity (`gpt-4.1` not `gpt-41`). Test that Azure accepts dots in deployment names (likely does, as OpenAI model names use dots).

**Verification Needed**:
1. Check Azure portal — does deployment `gpt-41` actually exist in prod AI Services?
2. Check Container App env vars — is `CU_COMPLETION_DEPLOYMENT` set? (Not in Bicep envVars currently)
3. Test Bicep deployment with `name: 'gpt-4.1'` to confirm Azure accepts it
4. Verify `update_defaults()` logs in production — does it log success or warning?

**Additional Findings**:
- Container App env vars (Bicep line 131-138) do NOT include `CU_COMPLETION_DEPLOYMENT` or `CU_EMBEDDING_DEPLOYMENT`
- Config uses defaults: `cu_completion_deployment = "gpt-41"` and `cu_embedding_deployment = "text-embedding-3-large"`
- If env vars aren't set, code uses defaults which may not match actual deployment names
- **Missing env vars**: Should set `CU_COMPLETION_DEPLOYMENT=gpt-41` (or `gpt-4.1` after fix) in Container App config
