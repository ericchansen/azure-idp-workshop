# Deployment Guide

## Architecture

The workshop deploys to **Azure Container Apps** via GitHub Actions using **OIDC federation** — no long-lived secrets are stored in GitHub.

```
GitHub Actions  ──OIDC──▶  Azure (UAMI: idp-deploy)  ──deploys──▶  Container App
                                                                      │
                                                              uses UAMI: idp-id
                                                              (runtime identity)
```

### Identities

| Identity | Type | Purpose |
|----------|------|---------|
| `idp-deploy` | User-Assigned Managed Identity | Authenticates the CI/CD pipeline to Azure via OIDC |
| `idp-id` | User-Assigned Managed Identity | Runtime identity for the container app (accesses AI Services, Storage, etc.) |

### Federated Identity Credentials (FICs)

FICs are defined in Bicep (`infra/modules/deploy-identity.bicep`) using the **immutable subject format** with embedded owner and repository IDs, so renaming or transferring the repo won't break deployments.

| FIC Name | Subject | Matches When |
|----------|---------|-------------|
| `github-main` | `repo:ericchansen@5395779/azure-idp-workshop@1167677240:ref:refs/heads/main` | Push to `main` branch |
| `github-production` | `repo:ericchansen@5395779/azure-idp-workshop@1167677240:environment:production` | Deploy to `production` environment |

The immutable format embeds numeric IDs after `@` separators (`owner@owner_id/repo@repo_id`), so even if the repository or owner is renamed, the subject claim still matches. This is enabled by setting `use_immutable_subject: true` on the GitHub repo's OIDC configuration.

## Workflows

| Workflow | File | Trigger | What It Does |
|----------|------|---------|-------------|
| CI | `ci.yml` | Push/PR to `main` | Lint, test, Docker build, structural E2E |
| Deploy Production | `deploy-prod.yml` | CI success on `main` | Deploy infra + app to production, smoke test |
| Dependabot Auto-Merge | `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merge non-major updates |

## Initial Setup

### Prerequisites

- Azure CLI (`az`) authenticated with sufficient permissions
- GitHub CLI (`gh`) authenticated
- The `AZURE_TENANT_ID` and `AZURE_SUBSCRIPTION_ID` repo secrets configured

### Bootstrap (one-time)

1. **Create the resource group:**
   ```bash
   az group create --name rg-idp-workshop --location eastus
   ```

2. **Deploy infrastructure** (creates both managed identities + FICs):
   ```bash
   az deployment group create \
     --resource-group rg-idp-workshop \
     --template-file infra/main.bicep \
     --parameters environmentName=prod acrName=idpworkshopacr
   ```

3. **Grant the deploy identity permissions:**
   ```bash
   DEPLOY_PRINCIPAL_ID=$(az identity show \
     --name idp-deploy \
     --resource-group rg-idp-workshop \
     --query principalId -o tsv)
   RG_SCOPE=$(az group show --name rg-idp-workshop --query id -o tsv)

   # Contributor
   az role assignment create \
     --assignee-object-id "$DEPLOY_PRINCIPAL_ID" \
     --assignee-principal-type ServicePrincipal \
     --role "b24988ac-6180-42a0-ab88-20f7382dd24c" \
     --scope "$RG_SCOPE"

   # User Access Administrator
   az role assignment create \
     --assignee-object-id "$DEPLOY_PRINCIPAL_ID" \
     --assignee-principal-type ServicePrincipal \
     --role "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9" \
     --scope "$RG_SCOPE"

   # AcrPush
   az role assignment create \
     --assignee-object-id "$DEPLOY_PRINCIPAL_ID" \
     --assignee-principal-type ServicePrincipal \
     --role "8311e382-0749-4cb8-b61a-304f252e45ec" \
     --scope "$RG_SCOPE"
   ```

4. **Enable immutable OIDC subjects on GitHub:**
   ```bash
   echo '{"use_default": false, "use_immutable_subject": true}' | \
     gh api repos/ericchansen/azure-idp-workshop/actions/oidc/customization/sub \
       --method PUT --input -
   ```

5. **Set the `AZURE_CLIENT_ID` repo secret** to the deploy identity's client ID:
   ```bash
   DEPLOY_CLIENT_ID=$(az identity show \
     --name idp-deploy \
     --resource-group rg-idp-workshop \
     --query clientId -o tsv)

   gh secret set AZURE_CLIENT_ID --body "$DEPLOY_CLIENT_ID"
   ```

6. **Verify** by triggering a deployment:
   ```bash
   gh workflow run "Deploy Production"
   ```

## Troubleshooting

### "AADSTS700024: Client assertion is not within its valid time range"
The OIDC token has expired. This usually means the workflow step took too long. The `azure/login` action handles token refresh, but long-running steps between login and Azure CLI usage can cause this.

### "AADSTS70021: No matching federated identity record found"
The OIDC token's `sub` claim doesn't match any FIC on the identity. Check:
1. Is `use_immutable_subject` enabled? `gh api repos/ericchansen/azure-idp-workshop/actions/oidc/customization/sub`
2. Do the FIC subjects match? `az identity federated-credential list --identity-name idp-deploy --resource-group rg-idp-workshop`
3. Is the workflow running from the expected branch/environment?
4. Does the subject format match? Immutable format is `repo:owner@owner_id/repo@repo_id:context`

### "AuthorizationFailed" errors
The deploy identity doesn't have the required RBAC roles. Re-run the role assignment commands from the bootstrap section above.
