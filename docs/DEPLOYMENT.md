# Deployment Guide

## Architecture

The workshop deploys to **Azure Container Apps** via GitHub Actions using **OIDC federation** — no long-lived secrets are stored in GitHub.

```
GitHub Actions  ──OIDC──▶  App Registration (github-azure-idp-workshop)  ──deploys──▶  Container App
                                                                                          │
                                                                                  uses UAMI: idp-id
                                                                                  (runtime identity)
```

### Identities

| Identity | Type | Purpose |
|----------|------|---------|
| `github-azure-idp-workshop` | App Registration (Entra ID) | Authenticates the CI/CD pipeline to Azure via OIDC |
| `idp-id` | User-Assigned Managed Identity | Runtime identity for the container app (accesses AI Services, Storage, etc.) |

### Federated Identity Credentials (FICs)

FICs are configured on the app registration using the **immutable subject format** with embedded owner and repository IDs, so renaming or transferring the repo won't break deployments.

| FIC Name | Subject | Matches When |
|----------|---------|-------------|
| `github-main` | `repo:ericchansen@5395779/azure-idp-workshop@1167677240:ref:refs/heads/main` | Push to `main` branch |
| `github-production` | `repo:ericchansen@5395779/azure-idp-workshop@1167677240:environment:production` | Deploy to `production` environment |
| `github-pr` | `repo:ericchansen@5395779/azure-idp-workshop@1167677240:pull_request` | Pull request workflows |

The immutable format embeds numeric IDs after `@` separators (`owner@owner_id/repo@repo_id`), so even if the repository or owner is renamed, the subject claim still matches. This is enabled by setting `use_immutable_subject: true` on the GitHub repo's OIDC configuration.

## Workflows

| Workflow | File | Trigger | What It Does |
|----------|------|---------|-------------|
| CI | `ci.yml` | Push/PR to `main` | Lint, test, Docker build, structural E2E |
| Deploy Production | `deploy-prod.yml` | CI success on `main` | Deploy infra + app to production, smoke test |
| Dependabot Auto-Merge | `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merge non-major updates |

## Environment Secrets

The `production` GitHub environment holds:

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | App registration client ID (`eb52dbf3-e6b9-46fd-a6a7-a38ec0fc2434`) |
| `AZURE_TENANT_ID` | Entra ID tenant (`9c74def4-ef0a-418a-8dc7-1e7a1e85ce10`) |
| `AZURE_SUBSCRIPTION_ID` | Target subscription for deployments |

> **Important:** Environment-level secrets override repo-level secrets. Always use `gh secret set --env production` to update these.

## OIDC Subject Configuration

Immutable subjects are enabled on the repo:

```bash
# Verify current config
gh api repos/ericchansen/azure-idp-workshop/actions/oidc/customization/sub
# Expected: {"use_default":true,"use_immutable_subject":true,"sub_claim_prefix":"repo:ericchansen@5395779/azure-idp-workshop@1167677240"}
```

## Troubleshooting

### "AADSTS70021: No matching federated identity record found"
The OIDC token's `sub` claim doesn't match any FIC on the app registration. Check:
1. Is `use_immutable_subject` enabled? `gh api repos/ericchansen/azure-idp-workshop/actions/oidc/customization/sub`
2. Do the FIC subjects match? `az ad app federated-credential list --id eb52dbf3-e6b9-46fd-a6a7-a38ec0fc2434`
3. Is the workflow running from the expected branch/environment?
4. Does the subject format match? Immutable format is `repo:owner@owner_id/repo@repo_id:context`

### "AADSTS700024: Client assertion is not within its valid time range"
The OIDC token has expired. This usually means the workflow step took too long. The `azure/login` action handles token refresh, but long-running steps between login and Azure CLI usage can cause this.

### "AuthorizationFailed" errors
The app registration's service principal doesn't have the required RBAC roles on the resource group.
