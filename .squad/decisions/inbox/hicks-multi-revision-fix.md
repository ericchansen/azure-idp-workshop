# Decision: Enable Multi-Revision Mode for Container App

**Author:** Hicks (Backend Dev)
**Date:** 2025-07-15
**Status:** Implemented

## Context

PR preview URLs (`---pr-N` label routing) were timing out because the Container App was deployed with `activeRevisionsMode: 'Single'`. In single-revision mode, a PR deployment replaces the production revision entirely, and label-based URLs don't resolve.

## Decision

Switch to `activeRevisionsMode: 'Multiple'` for all environments. This is the only mode that supports ACA label-based revision routing.

## Changes

1. **Bicep**: Added `activeRevisionsMode` parameter to `container-app.bicep`, set to `'Multiple'` from `main.bicep`
2. **Staging workflow**: Added runtime `revision set-mode` guard, production traffic pinning after PR revision creation
3. **Prod workflow**: Added explicit `latest=100` traffic routing after Bicep deploy (multi-revision mode doesn't auto-route)

## Trade-offs

- **Pro**: PR preview URLs now work; production traffic is explicitly protected
- **Con**: Old revisions accumulate and need cleanup (the existing deactivation logic handles this)
- **Risk**: If `az containerapp ingress traffic set` fails, traffic could split — mitigated with `|| true` fallback

## Impact

- Affects: `infra/modules/container-app.bicep`, `infra/main.bicep`, `deploy-stage.yml`, `deploy-prod.yml`
- Does NOT affect: Python source, templates, or test files
