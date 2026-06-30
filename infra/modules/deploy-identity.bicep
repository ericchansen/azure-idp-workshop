// Deploy Identity — User-Assigned Managed Identity for GitHub Actions OIDC
//
// This identity authenticates the CI/CD pipeline to Azure via OIDC federation.
// Federated Identity Credentials use the immutable subject format with embedded
// owner and repository IDs so that renaming or transferring the repo won't
// break deployments.
//
// Immutable subject format:
//   repo:<owner>@<owner_id>/<repo>@<repo_id>:<context>

@description('Name of the deploy managed identity')
param identityName string

@description('Azure region')
param location string

@description('GitHub repository owner (e.g., ericchansen)')
param repositoryOwner string

@description('Immutable GitHub repository owner ID (numeric). Obtain with: gh api repos/{owner}/{repo} --jq .owner.id')
param repositoryOwnerId int

@description('GitHub repository name (e.g., azure-idp-workshop)')
param repositoryName string

@description('Immutable GitHub repository ID (numeric). Obtain with: gh api repos/{owner}/{repo} --jq .id')
param repositoryId int

@description('Resource tags')
param tags object = {}

// ── Computed ────────────────────────────────────────────────────────────────

var subjectPrefix = 'repo:${repositoryOwner}@${repositoryOwnerId}/${repositoryName}@${repositoryId}'

// ── Managed Identity ────────────────────────────────────────────────────────

resource deployIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

// ── Federated Identity Credentials (GitHub Actions OIDC) ────────────────────

resource ficMain 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: deployIdentity
  name: 'github-main'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: '${subjectPrefix}:ref:refs/heads/main'
    audiences: ['api://AzureADTokenExchange']
  }
}

resource ficProduction 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: deployIdentity
  name: 'github-production'
  dependsOn: [ficMain]
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: '${subjectPrefix}:environment:production'
    audiences: ['api://AzureADTokenExchange']
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output clientId string = deployIdentity.properties.clientId
output principalId string = deployIdentity.properties.principalId
output identityName string = deployIdentity.name
