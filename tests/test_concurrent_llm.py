"""
Tests for concurrent LLM action.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.actions.concurrent_llm import evaluation_sub_agent_action


@pytest.mark.asyncio
async def test_concurrent_llm_action_success():
    """Test successful concurrent LLM calls."""
    
    # Mock httpx response
    mock_response_data = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 100}
    }
    
    with patch("src.actions.concurrent_llm.LLM_API_KEY", "test-api-key"), \
         patch("src.actions.concurrent_llm.LLM_BASE_URL", "https://api.openai.com/v1"), \
         patch("src.actions.concurrent_llm.LLM_MODEL", "gpt-3.5-turbo"), \
         patch("httpx.AsyncClient") as mock_client_class:
        
        # Create an async context manager mock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = lambda: None
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = ""
        mock_client.post.return_value = mock_response
        
        # Set up the context manager properly
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client
        mock_client_instance.__aexit__.return_value = None
        mock_client_class.return_value = mock_client_instance
        
        result = await evaluation_sub_agent_action(
            context="Test context",
            num_calls=2,
            system_prompt="Test prompt"
        )
        
        assert len(result) == 2
        assert all(r["success"] for r in result)
        assert all(r["response"] == "Test response" for r in result)
        assert all(r["tokens_used"] == 100 for r in result)


@pytest.mark.asyncio
async def test_concurrent_llm_action_missing_api_key():
    """Test error handling when API key is missing."""
    
    with patch("src.actions.concurrent_llm.LLM_API_KEY", None), \
         pytest.raises(ValueError, match="LLM API key is required"):
        await evaluation_sub_agent_action(
            context="Test context",
            num_calls=1,
            system_prompt="Test prompt"
        )


@pytest.mark.asyncio
async def test_concurrent_llm_action_with_failures():
    """Test handling of partial failures."""
    
    call_count = 0
    
    def create_mock_response():
        nonlocal call_count
        call_count += 1
        mock_response = Mock()
        
        if call_count == 1:
            # First call succeeds
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Success"}}],
                "usage": {"total_tokens": 50}
            }
            mock_response.raise_for_status = lambda: None
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = ""
        else:
            # Second call fails
            def raise_error():
                raise Exception("API Error")
            mock_response.raise_for_status = raise_error
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = ""
        
        return mock_response
    
    with patch("src.actions.concurrent_llm.LLM_API_KEY", "test-api-key"), \
         patch("src.actions.concurrent_llm.LLM_BASE_URL", "https://api.openai.com/v1"), \
         patch("src.actions.concurrent_llm.LLM_MODEL", "gpt-3.5-turbo"), \
         patch("httpx.AsyncClient") as mock_client_class:
        
        mock_client = AsyncMock()
        mock_client.post.side_effect = lambda *args, **kwargs: create_mock_response()
        
        # Set up the context manager properly
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client
        mock_client_instance.__aexit__.return_value = None
        mock_client_class.return_value = mock_client_instance
        
        result = await evaluation_sub_agent_action(
            context="Test context",
            num_calls=2,
            system_prompt="Test prompt"
        )
        
        assert len(result) == 2
        successful_calls = [r for r in result if r["success"]]
        failed_calls = [r for r in result if not r["success"]]
        assert len(successful_calls) == 1
        assert len(failed_calls) == 1
        assert successful_calls[0]["response"] == "Success"