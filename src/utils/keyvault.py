"""
Azure Key Vault utility for retrieving secrets using Azure CLI authentication.
"""

import logging
import os

from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


class KeyVaultClient:
    """Azure Key Vault client using Azure CLI authentication."""
    
    def __init__(self, vault_url: str | None = None):
        """Initialize Key Vault client.
        
        Args:
            vault_url: Azure Key Vault URL. If not provided, reads from AZURE_KEY_VAULT_URL env var.
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        if not self.vault_url:
            raise ValueError("AZURE_KEY_VAULT_URL environment variable is required")
        
        # Use Azure CLI credential for authentication
        self.credential = AzureCliCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
        
        logger.info(f"Initialized Key Vault client for: {self.vault_url}")
    
    def get_secret(self, secret_name: str) -> str | None:
        """Retrieve a secret from Key Vault.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Secret value if found, None otherwise
        """
        try:
            logger.debug(f"Retrieving secret: {secret_name}")
            secret = self.client.get_secret(secret_name)
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret.value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
            return None


def get_llm_api_key() -> str | None:
    """Get LLM API key from Azure Key Vault.
    
    Returns:
        LLM API key if available, None otherwise
    """
    try:
        secret_name = os.getenv("LLM_API_KEY_SECRET_NAME", "llm-api-key")
        kv_client = KeyVaultClient()
        return kv_client.get_secret(secret_name)
    except Exception as e:
        logger.warning(f"Could not retrieve LLM API key from Key Vault: {str(e)}")
        # Fallback to environment variable
        return os.getenv("LLM_API_KEY")