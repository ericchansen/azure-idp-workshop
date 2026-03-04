// Azure AI Services — Foundry-compatible with model deployments
// Supports both Content Understanding and Document Intelligence

@description('AI Services account name')
param name string

@description('Location')
param location string = resourceGroup().location

param tags object = {}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

// GPT-4.1 deployment (required for CU custom analyzers)
resource gpt41 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: 'gpt-4.1'
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

// Text embedding deployment (required for CU)
resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiServices
  name: 'text-embedding-3-large'
  dependsOn: [gpt41]
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
  }
}

output endpoint string = aiServices.properties.endpoint
output name string = aiServices.name
