"""
Unit tests for config.py
"""

import os
from unittest.mock import patch

import pytest

from src.config import load_config


def test_load_config_success():
    """Test successful config loading with all required environment variables."""
    with patch.dict(
        os.environ,
        {
            "MCP_SERVER_AUTH_KEY": "test_auth_key",
            "LOG_LEVEL": "DEBUG",  # Explicitly set to test default behavior
        },
    ):
        config = load_config()

        assert config.MCP_SERVER_AUTH_KEY == "test_auth_key"
        assert config.LOG_LEVEL == "DEBUG"  # default value
        assert config.ENVIRONMENT == "development"  # default value


def test_load_config_missing_required_key():
    """Test config validation fails when required environment variables are missing."""
    # Override system env vars by setting them to empty string, which should be treated as 
    # missing
    with patch.dict(
        os.environ,
        {
            "MCP_SERVER_AUTH_KEY": "",
        },
        clear=True,
    ):
        with patch("src.config.load_dotenv"):
            with pytest.raises(ValueError) as exc_info:
                load_config()

            assert "Missing required configuration" in str(exc_info.value)
            assert "MCP_SERVER_AUTH_KEY" in str(exc_info.value)


