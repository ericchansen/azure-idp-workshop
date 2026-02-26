// Azure Container Registry — shared across environments

@description('ACR name (globally unique, alphanumeric only)')
param name string

@description('Location')
param location string = resourceGroup().location

@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

param tags object = {}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output acrId string = acr.id
output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
