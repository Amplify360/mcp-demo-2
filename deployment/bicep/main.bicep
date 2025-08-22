@description('The base name for resources')
param baseName string = 'mcp-sse'

@description('The environment (dev, test, prod)')
param environment string = 'dev'

@description('The location for all resources')
param location string = resourceGroup().location

@description('The Azure region code')
param regionCode string = 'weu'

@description('The name of the resource group')
param resourceGroupName string = 'rg-${baseName}-${environment}-${regionCode}'

@description('The MCP Server Auth Key')
@secure()
param mcpServerAuthKey string

@description('The Postmark API Key')
@secure()
param postmarkApiKey string

@description('The sender email address')
param senderEmail string

@description('The test email recipients')
param testEmailRecipients string = ''

// Define resource naming variables using standard abbreviations
var containerAppName = 'ca-${baseName}-${environment}-${regionCode}'
var containerAppEnvName = 'cae-${baseName}-${environment}-${regionCode}'
var logAnalyticsName = 'log-${baseName}-${environment}-${regionCode}'
var containerRegistryName = 'cr${replace(baseName, '-', '')}${environment}${regionCode}'
var imageName = '${containerRegistryName}.azurecr.io/${baseName}:latest'

// Log analytics workspace for container app monitoring
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Container registry for storing container images
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-12-01-preview' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Container app environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-10-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Container app
resource containerApp 'Microsoft.App/containerApps@2022-10-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'mcp-server-auth-key'
          value: mcpServerAuthKey
        }
        {
          name: 'postmark-api-key'
          value: postmarkApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: imageName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'MCP_SERVER_AUTH_KEY'
              secretRef: 'mcp-server-auth-key'
            }
            {
              name: 'POSTMARK_API_KEY'
              secretRef: 'postmark-api-key'
            }
            {
              name: 'SENDER_EMAIL'
              value: senderEmail
            }
            {
              name: 'TEST_EMAIL_RECIPIENTS'
              value: testEmailRecipients
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'FILE_LOGGING'
              value: 'true'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// Output the container app URL and resource names
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppName string = containerAppName
output containerRegistryName string = containerRegistryName
output logAnalyticsName string = logAnalyticsName 
