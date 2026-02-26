using 'main.bicep'

param environmentName = 'stage'
param acrName = 'idpworkshopacr'
param location = 'eastus'
param aiServicesName = 'idp-workshop-ai'
param storageAccountName = 'idpworkshopstorage'
param logAnalyticsWorkspaceName = 'idp-workshop-logs'
param tags = {
  project: 'azure-idp-workshop'
  environment: 'stage'
}
