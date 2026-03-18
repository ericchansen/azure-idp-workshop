// SimpleL7Proxy — Intelligent LLM request router
//
// Deploys SimpleL7Proxy as a Container App for PTU-first routing
// with PAYG fallback. Used by Module 4 to demonstrate batch processing
// at scale with cost-effective provisioned throughput.
//
// Reference: https://github.com/microsoft/SimpleL7Proxy

@description('Proxy Container App name')
param name string = 'idp-proxy'

@description('Location for the proxy')
param location string = resourceGroup().location

@description('Container Apps Environment ID')
param environmentId string

@description('User-assigned managed identity resource ID')
param userAssignedIdentityId string

@description('PTU endpoint (primary — provisioned throughput)')
param ptuEndpoint string

@description('PAYG endpoint (fallback — pay-as-you-go)')
param paygEndpoint string

param tags object = {}

resource proxy 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { purpose: 'llm-proxy' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          name: 'proxy'
          image: 'ghcr.io/microsoft/simplel7proxy:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            // Proxy config — environment variable based
            { name: 'Port', value: '8000' }
            { name: 'Workers', value: '50' }
            { name: 'MaxQueueLength', value: '500' }

            // Backend 1: PTU (primary — provisioned throughput, no per-call cost)
            {
              name: 'Host1'
              value: 'host=${ptuEndpoint};usemi=true;mode=direct;path=/'
            }

            // Backend 2: PAYG (fallback — pay-as-you-go when PTU is saturated)
            {
              name: 'Host2'
              value: 'host=${paygEndpoint};usemi=true;mode=direct;path=/'
            }

            // Load balancing — latency-based prefers the faster (non-throttled) endpoint
            { name: 'LoadBalanceMode', value: 'latency' }
            { name: 'IterationMode', value: 'MultiPass' }
            { name: 'MaxAttempts', value: '10' }

            // Circuit breaker — auto-failover when PTU is overloaded
            { name: 'CBErrorThreshold', value: '20' }
            { name: 'CBTimeslice', value: '60' }
            { name: 'AcceptableStatusCodes', value: '200,201,202,204,401,409' }

            // Health probes
            { name: 'PollInterval', value: '5000' }
            { name: 'PollTimeout', value: '3000' }

            // Timeouts
            { name: 'Timeout', value: '60000' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: 8000
              }
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

@description('Proxy internal URL (Container Apps internal FQDN)')
output internalUrl string = 'https://${proxy.properties.configuration.ingress.fqdn}'

@description('Proxy resource name')
output name string = proxy.name
