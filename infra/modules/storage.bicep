// Storage account

@description('Storage account name (globally unique, alphanumeric, lowercase)')
param name string

@description('Location')
param location string = resourceGroup().location

param tags object = {}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

output storageId string = storage.id
output storageName string = storage.name
output blobEndpoint string = storage.properties.primaryEndpoints.blob
