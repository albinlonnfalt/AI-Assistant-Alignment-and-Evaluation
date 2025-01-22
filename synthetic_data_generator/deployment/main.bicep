param name string
param location string = resourceGroup().location

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: '${name}-environment'

  location: location
  properties: {}
}

resource containerAppIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${name}-identity'
  location: location
}
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: '${name}acr'
  sku: {
    name: 'Basic'
  }
  location: location
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2020-10-01-preview' = {
  name: guid(containerAppIdentity.id, 'AcrPull')
  // scope: acr
  properties: {
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
    principalId: containerAppIdentity.properties.principalId
  }
}
