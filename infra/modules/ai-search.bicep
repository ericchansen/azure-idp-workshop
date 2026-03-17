// Azure AI Search — Basic tier with semantic search
//
// Used by the workshop's Module 3 to demonstrate document indexing and search.

@description('AI Search service name (globally unique)')
param name string

@description('Location for the search service')
param location string = resourceGroup().location

@description('SKU — basic supports semantic search')
@allowed(['free', 'basic', 'standard'])
param sku string = 'basic'

param tags object = {}

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    semanticSearch: 'standard'
    hostingMode: 'default'
    replicaCount: 1
    partitionCount: 1
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

@description('AI Search endpoint URL')
output endpoint string = 'https://${name}.search.windows.net'

@description('AI Search service name')
output name string = searchService.name

@description('AI Search resource ID')
output id string = searchService.id
