#!/bin/bash
set -e

# Determine if this is an update or initial deployment
IS_UPDATE=false

# Default values
BASE_NAME="${BASE_NAME:-mcp-sse}"
ENVIRONMENT="dev"
REGION_CODE="${REGION_CODE:-weu}"
RESOURCE_GROUP="rg-${BASE_NAME}-${ENVIRONMENT}-${REGION_CODE}"
LOCATION="westeurope"

# Setup QEMU for cross-platform builds (for M1/ARM Macs)
echo "Setting up QEMU for cross-platform builds..."
docker run --privileged --rm tonistiigi/binfmt --install all

# Setup buildx for better cross-platform support
echo "Setting up Docker buildx..."
docker buildx create --name multiarch-builder --use || true
docker buildx inspect --bootstrap

# Function to redeploy code updates only
function redeploy_code() {
  local base_name=$1
  local environment=$2
  local resource_group=$3
  local container_registry_name=$4
  
  echo "Redeploying code updates only (no infrastructure changes)..."
  
  # Build container image using buildx for proper platform targeting
  echo "Building container image..."
  docker buildx build --platform linux/amd64 --load -t "${base_name}:latest" ../..
  
  # Log in to container registry
  echo "Logging in to container registry..."
  REGISTRY_USERNAME=$(az acr credential show --name "$container_registry_name" --query "username" -o tsv)
  REGISTRY_PASSWORD=$(az acr credential show --name "$container_registry_name" --query "passwords[0].value" -o tsv)
  echo "Authenticating with registry (credentials masked for security)"
  docker login "${container_registry_name}.azurecr.io" -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD" >/dev/null 2>&1
  
  # Tag and push container image
  echo "Tagging and pushing updated container image..."
  docker tag "${base_name}:latest" "${container_registry_name}.azurecr.io/${base_name}:latest"
  docker push "${container_registry_name}.azurecr.io/${base_name}:latest"
  
  # Get container app name
  CONTAINER_APP_NAME="ca-${base_name}-${environment}-${REGION_CODE}"
  
  # Restart the container app to pick up new image
  echo "Restarting container app to apply changes..."
  az containerapp update \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$resource_group" \
    --image "${container_registry_name}.azurecr.io/${base_name}:latest"
  
  echo "Code update deployment complete!"
  echo "Container App: $CONTAINER_APP_NAME"
}

# Load environment variables from .env file if it exists
if [ -f "../../.env" ]; then
  echo "Loading environment variables from .env file..."
  # Load env vars without echoing sensitive values
  set -a
  source ../../.env
  set +a
  
  # Use environment value from .env if available
  if [ -n "$ENVIRONMENT" ]; then
    echo "Using environment '${ENVIRONMENT}' from .env file"
  fi
else
  echo "Warning: .env file not found. Using default values."
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --resource-group)
      RESOURCE_GROUP="$2"
      shift
      shift
      ;;
    --location)
      LOCATION="$2"
      shift
      shift
      ;;
    --base-name)
      BASE_NAME="$2"
      shift
      shift
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift
      shift
      ;;
    --region-code)
      REGION_CODE="$2"
      shift
      shift
      ;;
    --update)
      IS_UPDATE=true
      shift
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Compute resource names using Azure naming convention
CONTAINER_APP_NAME="ca-${BASE_NAME}-${ENVIRONMENT}-${REGION_CODE}"
CONTAINER_APP_ENV_NAME="cae-${BASE_NAME}-${ENVIRONMENT}-${REGION_CODE}"
LOG_ANALYTICS_NAME="log-${BASE_NAME}-${ENVIRONMENT}-${REGION_CODE}"
CONTAINER_REGISTRY_NAME="cr${BASE_NAME//[-_]/}${ENVIRONMENT}${REGION_CODE}"

# Check if required environment variables are set
if [ -z "$MCP_SERVER_AUTH_KEY" ]; then
  echo "Error: MCP_SERVER_AUTH_KEY environment variable is not set"
  exit 1
fi

if [ -z "$POSTMARK_API_KEY" ]; then
  echo "Error: POSTMARK_API_KEY environment variable is not set"
  exit 1
fi

if [ -z "$SENDER_EMAIL" ]; then
  echo "Error: SENDER_EMAIL environment variable is not set"
  exit 1
fi

# Handle update mode
if [ "$IS_UPDATE" = true ]; then
  # Check if resource group exists
  if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo "Resource group '$RESOURCE_GROUP' exists. Proceeding with code update."
    redeploy_code "$BASE_NAME" "$ENVIRONMENT" "$RESOURCE_GROUP" "$CONTAINER_REGISTRY_NAME"
    exit 0
  else
    echo "Resource group '$RESOURCE_GROUP' not found. Cannot update."
    echo "Please run without --update flag to perform full deployment."
    exit 1
  fi
fi

# Create resource group if it doesn't exist
echo "Creating resource group '$RESOURCE_GROUP' in '$LOCATION'..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --tags "Application=${BASE_NAME}" "Environment=${ENVIRONMENT}"

# Build container image using buildx for proper platform targeting
echo "Building container image..."
docker buildx build --platform linux/amd64 --load -t "${BASE_NAME}:latest" ../..

# Create container registry if it doesn't exist
echo "Creating container registry '$CONTAINER_REGISTRY_NAME'..."
az acr create --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_REGISTRY_NAME" --sku Basic --admin-enabled true

# Log in to container registry
echo "Logging in to container registry..."
REGISTRY_USERNAME=$(az acr credential show --name "$CONTAINER_REGISTRY_NAME" --query "username" -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name "$CONTAINER_REGISTRY_NAME" --query "passwords[0].value" -o tsv)
echo "Authenticating with registry (credentials masked for security)"
docker login "${CONTAINER_REGISTRY_NAME}.azurecr.io" -u "$REGISTRY_USERNAME" -p "$REGISTRY_PASSWORD" >/dev/null 2>&1

# Tag and push container image
echo "Tagging and pushing container image..."
docker tag "${BASE_NAME}:latest" "${CONTAINER_REGISTRY_NAME}.azurecr.io/${BASE_NAME}:latest"
docker push "${CONTAINER_REGISTRY_NAME}.azurecr.io/${BASE_NAME}:latest"

# Deploy Azure resources using Bicep
echo "Deploying Azure resources using Bicep..."
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file main.bicep \
  --parameters \
    baseName="$BASE_NAME" \
    environment="$ENVIRONMENT" \
    regionCode="$REGION_CODE" \
    location="$LOCATION" \
    resourceGroupName="$RESOURCE_GROUP" \
    mcpServerAuthKey="$MCP_SERVER_AUTH_KEY" \
    postmarkApiKey="$POSTMARK_API_KEY" \
    senderEmail="$SENDER_EMAIL" \
    testEmailRecipients="$TEST_EMAIL_RECIPIENTS"

# Get deployment outputs
echo "Getting deployment outputs..."
CONTAINER_APP_URL=$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name main \
  --query "properties.outputs.containerAppUrl.value" \
  --output tsv)

CONTAINER_APP_NAME=$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name main \
  --query "properties.outputs.containerAppName.value" \
  --output tsv)

echo "Deployment complete!"
echo "Container App: $CONTAINER_APP_NAME"
echo "Container App URL: $CONTAINER_APP_URL"
echo "Resource Group: $RESOURCE_GROUP"
echo ""
echo "For future code updates, run: ./deploy.sh --update" 