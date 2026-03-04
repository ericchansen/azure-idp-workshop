# CU Production Failure — Model Deployment Name Mismatch

**Date**: 2025-02-28  
**By**: Bishop (Azure AI Expert)  
**Status**: Ready for Review → Eric Hansen  
**Priority**: HIGH (3/9 smoke tests failing in production)

## Problem

CU (Content Understanding) custom analysis failing in production. Module 2 smoke test times out waiting for CU results. Root cause: **model deployment name mismatch**.

## Root Cause

The CU SDK code hardcodes model identifier as `"gpt-4.1"` (with dot):
- `content_understanding.py` line 146: `"gpt-4.1": settings.cu_completion_deployment`
- `content_understanding.py` line 168: `"models": {"completion": "gpt-4.1"}`

But Bicep deploys the model as `name: 'gpt-41'` (no dot):
- `infra/modules/ai-services.bicep` line 29: `name: 'gpt-41'`

**Result**: CU SDK asks Azure for completion model `"gpt-4.1"` → Azure can't find it (only has `"gpt-41"`) → analysis fails.

## Why DI Works, CU Fails

- **DI**: Uses prebuilt analyzers (`prebuilt-layout`, `prebuilt-invoice`) that don't require custom GPT deployments. Just needs AI Services endpoint.
- **CU prebuilt**: May work (uses prebuilt analyzers like `prebuilt-layout`)
- **CU custom**: **ALWAYS fails** — creates custom analyzer with `"completion": "gpt-4.1"` model reference, Azure can't find the deployment

## Impact

- Module 1 (DI layout vs CU layout): **PASSES** — both use prebuilt analyzers
- Module 2 (DI layout vs CU custom): **FAILS** — CU custom needs GPT completion model
- All CU `/api/cu/custom` endpoints fail in production

## Recommended Fix (Option A)

**Change Bicep deployment name to match SDK expectations:**

```bicep
// infra/modules/ai-services.bicep line 29
resource gpt41 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: 'gpt-4.1'  // ← was 'gpt-41'
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
    }
  }
}
```

**Why this is best:**
- Model version identifiers should use dots for clarity (`gpt-4.1` not `gpt-41`)
- SDK code stays clean and follows Azure conventions
- Config default already matches: `cu_completion_deployment: str = "gpt-41"` → change to `"gpt-4.1"`

## Alternative Fixes

**Option B**: Change code to match Bicep (quick fix but less clean)
- Change `content_understanding.py` line 146 & 168: `"gpt-4.1"` → `"gpt-41"`
- Pro: No infra change
- Con: Hardcoded string in two places, model identifier doesn't match actual version

**Option C**: Make model identifier configurable (over-engineered)
- Add `settings.cu_completion_model_id` config variable
- Pro: Most flexible
- Con: Adds complexity

## Additional Required Changes

1. **Add CU env vars to Container App config** (Bicep):
   ```bicep
   // infra/modules/container-app.bicep envVars array
   { name: 'CU_COMPLETION_DEPLOYMENT', value: 'gpt-4.1' }
   { name: 'CU_EMBEDDING_DEPLOYMENT', value: 'text-embedding-3-large' }
   ```
   Currently missing — Container App uses hardcoded config defaults.

2. **Update config defaults** (if using Option A):
   ```python
   # src/workshop/config.py
   cu_completion_deployment: str = "gpt-4.1"  # ← was "gpt-41"
   ```

## Verification Steps

Before deploying fix:
1. Check Azure portal — confirm deployment name in prod AI Services resource
2. Test Bicep deployment with `name: 'gpt-4.1'` in dev/stage (confirm Azure accepts dots)
3. Check Container App logs for `update_defaults()` messages (success or warning?)

After deploying fix:
1. Run smoke tests: `npx playwright test --grep Smoke --project="Desktop Edge"`
2. Verify Module 2 CU custom analysis completes successfully
3. Check API trace viewer — CU usage/token counts should appear

## Files to Change

- `infra/modules/ai-services.bicep` — deployment name
- `infra/modules/container-app.bicep` — add CU env vars
- `src/workshop/config.py` — update default
- Possibly: `content_understanding.py` if using Option B or C

## Confidence Level

**HIGH** — Evidence is clear:
- Code expects `"gpt-4.1"`, Bicep deploys `"gpt-41"`
- Module 2 smoke test fails exactly where CU custom is used
- DI works, CU custom fails — consistent with model deployment issue
- No other significant differences between DI and CU setup

## Next Steps

1. Eric reviews this analysis
2. Choose fix option (recommend Option A)
3. Test in staging first
4. Deploy to production
5. Re-run smoke tests to verify all 9 pass
