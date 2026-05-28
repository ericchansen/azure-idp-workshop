#!/usr/bin/env bash
# Bootstrap OIDC authentication for GitHub Actions → Azure deployments.
#
# This is a one-time setup script. It creates:
#   1. An Entra ID app registration + service principal
#   2. Federated credentials for GitHub Actions (main branch + production env)
#   3. Contributor role assignment on the target subscription
#
# After running, set these GitHub secrets in the "production" environment:
#   AZURE_CLIENT_ID      → from output
#   AZURE_TENANT_ID      → from output
#   AZURE_SUBSCRIPTION_ID → from output
#
# Usage:
#   SUBSCRIPTION_ID=<guid> GITHUB_REPO=owner/repo ./bootstrap-oidc.sh

set -euo pipefail

: "${SUBSCRIPTION_ID:?Set SUBSCRIPTION_ID}"
: "${GITHUB_REPO:?Set GITHUB_REPO (e.g., owner/repo)}"

APP_NAME="idp-workshop-deploy"
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "==> Creating app registration: $APP_NAME"
CLIENT_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --query appId -o tsv)

echo "==> Creating service principal"
OBJECT_ID=$(az ad sp create --id "$CLIENT_ID" --query id -o tsv 2>/dev/null || \
  az ad sp show --id "$CLIENT_ID" --query id -o tsv)

echo "==> Adding federated credential: main branch"
az ad app federated-credential create --id "$CLIENT_ID" --parameters "{
  \"name\": \"github-main\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_REPO}:ref:refs/heads/main\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" --output none

echo "==> Adding federated credential: production environment"
az ad app federated-credential create --id "$CLIENT_ID" --parameters "{
  \"name\": \"github-production\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_REPO}:environment:production\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" --output none

echo "==> Assigning Contributor on subscription"
az role assignment create \
  --assignee-object-id "$OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Contributor \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --output none

cat <<EOF

✅ Bootstrap complete

Set these GitHub secrets (production environment):
  AZURE_CLIENT_ID       = $CLIENT_ID
  AZURE_TENANT_ID       = $TENANT_ID
  AZURE_SUBSCRIPTION_ID = $SUBSCRIPTION_ID

EOF
