// Azure AI Services — Foundry-compatible with model deployments
// Supports both Content Understanding and Document Intelligence

@description('AI Services account name')
param name string

@description('Location')
param location string = resourceGroup().location

param tags object = {}

@description('Default CU completion model name')
param cuCompletionModelName string = 'gpt-5.2'

@description('Default CU completion deployment name')
param cuCompletionDeploymentName string = 'gpt-5.2'

@description('Default CU completion model version')
param cuCompletionModelVersion string = '2025-12-11'

@description('CU completion deployment SKU')
param cuCompletionDeploymentSkuName string = 'GlobalStandard'

@description('CU completion deployment capacity')
param cuCompletionDeploymentCapacity int = 10

@description('Deploy GPT-4.1 as a fallback completion model')
param deployGpt41Fallback bool = true

@description('CU embedding model name')
param cuEmbeddingModelName string = 'text-embedding-3-large'

@description('CU embedding deployment name')
param cuEmbeddingDeploymentName string = 'text-embedding-3-large'

@description('Foundry project name for portal authoring and model deployment UX. Set empty to skip project creation.')
param foundryProjectName string = ''

@description('Foundry project display name')
param foundryProjectDisplayName string = 'Patient Log Demo'

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

// Default completion deployment for CU custom analyzers
resource completion 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: cuCompletionDeploymentName
  sku: {
    name: cuCompletionDeploymentSkuName
    capacity: cuCompletionDeploymentCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: cuCompletionModelName
      version: cuCompletionModelVersion
    }
  }
}

// GPT-4.1 fallback while validating newer CU completion models.
// Serialized after the primary completion deployment: Cognitive Services
// rejects concurrent deployment operations on the same account (RequestConflict).
resource gpt41Fallback 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployGpt41Fallback && cuCompletionDeploymentName != 'gpt-4.1') {
  parent: aiServices
  name: 'gpt-4.1'
  dependsOn: [completion]
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

// Text embedding deployment (required for CU). Serialized after the prior
// model deployments so all account/deployments operations run sequentially.
resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: cuEmbeddingDeploymentName
  dependsOn: [completion, gpt41Fallback]
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: cuEmbeddingModelName
      version: '1'
    }
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = if (!empty(foundryProjectName)) {
  parent: aiServices
  name: foundryProjectName
  location: location
  tags: tags
  properties: {
    description: 'Patient treatment log Content Understanding demo project'
    displayName: foundryProjectDisplayName
  }
}

output endpoint string = aiServices.properties.endpoint
output name string = aiServices.name
output projectName string = foundryProjectName
output projectId string = !empty(foundryProjectName) ? foundryProject.id : ''
