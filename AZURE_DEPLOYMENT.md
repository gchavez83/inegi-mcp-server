# Deployment en Azure

Esta guía explica cómo desplegar el servidor MCP del INEGI en Azure.

## Opciones de Deployment

### Opción 1: Azure App Service (Recomendada)

#### Configurar Variables de Entorno en Azure Portal

1. Navega a tu App Service en Azure Portal
2. Ve a **Configuration** > **Application Settings**
3. Añade las siguientes variables:
   - `INEGI_INDICADORES_TOKEN`: Tu token de API de Indicadores
   - `INEGI_DENUE_TOKEN`: Tu token de API del DENUE

#### Deployment con Azure CLI

```bash
# Login en Azure
az login

# Crear App Service
az webapp up --name inegi-mcp-server --runtime PYTHON:3.10

# Configurar variables de entorno
az webapp config appsettings set --name inegi-mcp-server \
  --resource-group <tu-grupo-recursos> \
  --settings \
    INEGI_INDICADORES_TOKEN="tu-token-indicadores" \
    INEGI_DENUE_TOKEN="tu-token-denue"
```

### Opción 2: Azure Key Vault (Máxima Seguridad)

#### Paso 1: Crear Key Vault

```bash
# Crear Key Vault
az keyvault create \
  --name inegi-mcp-keyvault \
  --resource-group <tu-grupo-recursos> \
  --location eastus

# Añadir secretos
az keyvault secret set \
  --vault-name inegi-mcp-keyvault \
  --name "inegi-indicadores-token" \
  --value "tu-token-indicadores"

az keyvault secret set \
  --vault-name inegi-mcp-keyvault \
  --name "inegi-denue-token" \
  --value "tu-token-denue"
```

#### Paso 2: Configurar Managed Identity

```bash
# Habilitar Managed Identity en tu App Service
az webapp identity assign \
  --name inegi-mcp-server \
  --resource-group <tu-grupo-recursos>

# Dar permisos al App Service
az keyvault set-policy \
  --name inegi-mcp-keyvault \
  --object-id <managed-identity-principal-id> \
  --secret-permissions get list
```

#### Paso 3: Modificar código para usar Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Configurar cliente de Key Vault
credential = DefaultAzureCredential()
vault_url = "https://inegi-mcp-keyvault.vault.azure.net/"
client = SecretClient(vault_url=vault_url, credential=credential)

# Obtener secretos
indicadores_token = client.get_secret("inegi-indicadores-token").value
denue_token = client.get_secret("inegi-denue-token").value
```

### Opción 3: Azure Container Instances

```bash
# Crear container registry
az acr create --name inegimcp --resource-group <tu-grupo-recursos> --sku Basic

# Build y push de imagen
docker build -t inegimcp.azurecr.io/inegi-mcp:latest .
docker push inegimcp.azurecr.io/inegi-mcp:latest

# Deploy container
az container create \
  --name inegi-mcp-container \
  --resource-group <tu-grupo-recursos> \
  --image inegimcp.azurecr.io/inegi-mcp:latest \
  --environment-variables \
    INEGI_INDICADORES_TOKEN="tu-token" \
    INEGI_DENUE_TOKEN="tu-token"
```

## Azure DevOps Pipeline

Ejemplo de pipeline para CI/CD:

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: inegi-tokens  # Variable group con tokens secretos

stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'
          
          - script: |
              pip install -e .
            displayName: 'Install dependencies'
  
  - stage: Deploy
    jobs:
      - job: DeployJob
        steps:
          - task: AzureWebApp@1
            inputs:
              azureSubscription: '<tu-subscription>'
              appName: 'inegi-mcp-server'
              package: '$(System.DefaultWorkingDirectory)'
              appSettings: |
                -INEGI_INDICADORES_TOKEN "$(INEGI_INDICADORES_TOKEN)"
                -INEGI_DENUE_TOKEN "$(INEGI_DENUE_TOKEN)"
```

## Seguridad

### Recomendaciones:
1. **Nunca** commits tokens en el código
2. Usa **Azure Key Vault** para producción
3. Habilita **Application Insights** para monitoreo
4. Configura **RBAC** apropiado
5. Usa **Managed Identities** cuando sea posible

## Monitoreo

Configurar Application Insights:

```bash
# Crear Application Insights
az monitor app-insights component create \
  --app inegi-mcp-insights \
  --location eastus \
  --resource-group <tu-grupo-recursos>

# Conectar con App Service
az webapp config appsettings set \
  --name inegi-mcp-server \
  --resource-group <tu-grupo-recursos> \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

## Troubleshooting

### Error: Token no encontrado
- Verifica que las variables de entorno estén configuradas correctamente en Azure Portal
- Revisa los logs: `az webapp log tail --name inegi-mcp-server`

### Error: Permisos de Key Vault
- Verifica que el Managed Identity tiene permisos en el Key Vault
- Revisa la política de acceso del Key Vault

## Recursos Adicionales
- [Azure App Service Documentation](https://learn.microsoft.com/azure/app-service/)
- [Azure Key Vault Documentation](https://learn.microsoft.com/azure/key-vault/)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/)
