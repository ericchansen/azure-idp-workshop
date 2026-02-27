// Azure IDP Workshop — Main Deployment
// Creates ALL resources from scratch in an isolated resource group.
//
// Resources created:
//   - AI Services (Foundry-compatible) + model deployments
//   - Storage account
//   - Log Analytics workspace
//   - ACR (shared)
//   - Container Apps Environment + Container App (per environment)
//   - User-Assigned Managed Identity + role assignments

targetScope = 'resourceGroup'

// ── Parameters ──────────────────────────────────────────────────────────────

@description('Environment name (prod, stage, etc.)')
param environmentName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Container image to deploy (e.g., myacr.azurecr.io/idp-workshop:sha-abc)')
param containerImage string = ''

@description('ACR name (globally unique)')
param acrName string

@description('AI Services account name')
param aiServicesName string = 'idp-workshop-ai'

@description('Storage account name')
param storageAccountName string = 'idpworkshopstorage'

@description('Log Analytics workspace name')
param logAnalyticsWorkspaceName string = 'idp-workshop-logs'

param tags object = {}

// ── Computed Names ──────────────────────────────────────────────────────────

var envSuffix = environmentName == 'prod' ? '' : '-${environmentName}'
var appEnvName = 'idp-cae${envSuffix}'
var appName = 'idp-workshop${envSuffix}'
var identityName = 'idp-id${envSuffix}'

// Well-known role definition GUIDs
var storageBlobDataContributorRole = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var cognitiveServicesUserRole = 'a97b65f3-24c7-4388-baec-2e87135dc908'
var acrPullRole = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// ── AI Services ─────────────────────────────────────────────────────────────

module aiServices 'modules/ai-services.bicep' = {
  name: 'ai-services'
  params: {
    name: aiServicesName
    location: location
    tags: tags
  }
}

// ── Storage ─────────────────────────────────────────────────────────────────

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageAccountName
    location: location
    tags: tags
  }
}

// ── Log Analytics ───────────────────────────────────────────────────────────

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    name: logAnalyticsWorkspaceName
    location: location
    tags: tags
  }
}

// ── ACR ─────────────────────────────────────────────────────────────────────

module acr 'modules/acr.bicep' = {
  name: 'acr-${acrName}'
  params: {
    name: acrName
    location: location
    tags: tags
  }
}

// ── Per-Environment: Managed Identity ───────────────────────────────────────

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: union(tags, { environment: environmentName })
}

// ── Role Assignments ────────────────────────────────────────────────────────

module roleStorage 'modules/role-assignment.bicep' = {
  name: 'role-storage-${environmentName}'
  params: {
    principalId: identity.properties.principalId
    roleDefinitionId: storageBlobDataContributorRole
  }
}

module roleCognitive 'modules/role-assignment.bicep' = {
  name: 'role-cognitive-${environmentName}'
  params: {
    principalId: identity.properties.principalId
    roleDefinitionId: cognitiveServicesUserRole
  }
}

module roleAcrPull 'modules/role-assignment.bicep' = {
  name: 'role-acr-pull-${environmentName}'
  params: {
    principalId: identity.properties.principalId
    roleDefinitionId: acrPullRole
  }
}

// ── Container Apps ──────────────────────────────────────────────────────────

module appEnv 'modules/container-app-env.bicep' = {
  name: 'cae-${environmentName}'
  params: {
    name: appEnvName
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    tags: union(tags, { environment: environmentName })
  }
}

module app 'modules/container-app.bicep' = if (!empty(containerImage)) {
  name: 'app-${environmentName}'
  dependsOn: [roleAcrPull]
  params: {
    name: appName
    location: location
    environmentId: appEnv.outputs.environmentId
    containerImage: containerImage
    acrLoginServer: acr.outputs.acrLoginServer
    userAssignedIdentityId: identity.id
    tags: union(tags, { environment: environmentName })
    activeRevisionsMode: 'Multiple'
    minReplicas: environmentName == 'prod' ? 1 : 0
    maxReplicas: environmentName == 'prod' ? 3 : 1
    secrets: []
    envVars: [
      { name: 'ENVIRONMENT', value: environmentName }
      { name: 'AI_SERVICES_ENDPOINT', value: aiServices.outputs.endpoint }
      { name: 'STORAGE_ACCOUNT_URL', value: storage.outputs.blobEndpoint }
      { name: 'LOG_LEVEL', value: environmentName == 'prod' ? 'INFO' : 'DEBUG' }
      { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
    ]
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output acrLoginServer string = acr.outputs.acrLoginServer
output appUrl string = !empty(containerImage) ? app.outputs.appUrl! : ''
output appFqdn string = !empty(containerImage) ? app.outputs.appFqdn! : ''
