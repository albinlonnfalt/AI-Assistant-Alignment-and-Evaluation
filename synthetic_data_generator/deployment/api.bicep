param location string = resourceGroup().location
param name string
var containerAppName = '${name}-api'
param containerImage string
@secure()
param azureOpenAIKey string
param azureOpenAIChatModel string 
param azureOpenAIApiVersion string
param azureOpenAIEndpoint string

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' existing = {
  name: '${name}-environment'

}

resource containerAppIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' existing = {
  name: '${name}-identity'
}
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: '${name}acr'

}


resource containerApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: containerAppName
  location: location
 

  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${containerAppIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      registries: [
        {
          identity: containerAppIdentity.id
          server: acr.properties.loginServer
        }
      ]
      secrets: [
        { name: 'azureopenaikey', value: azureOpenAIKey }
      ]
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'synthetic-data-generator-container'
          image: containerImage
          env: [
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azureopenaikey'
            }
            { name: 'AZURE_OPENAI_CHATMODEL', value: azureOpenAIChatModel }
            { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAIApiVersion }
            {name:'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint}
          ]
          resources: {
            cpu: '0.5'
            memory: '1.0Gi'
          }
        }
      ]
    }
  }
}



output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
