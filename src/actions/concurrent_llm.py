"""
Concurrent LLM calls action implementation.
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from ..utils.keyvault import get_llm_api_key

logger = logging.getLogger(__name__)

# Global configuration loaded from key vault and environment
LLM_API_KEY = get_llm_api_key()
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")


async def evaluation_sub_agent_action(
    context: str,
    num_calls: int = 3,
    system_prompt: str = "You are a helpful assistant.",
) -> dict[str, Any]:
    """
    Make concurrent calls to an LLM with given context and system prompt.
    
    Args:
        context: The context to send to the LLM
        num_calls: Number of concurrent calls to make (default: 3)
        system_prompt: Fixed system prompt to send with each call
    
    Returns:
        Dictionary with results list and metadata
    """
    logger.info(f"Starting {num_calls} concurrent LLM calls")
    
    if not LLM_API_KEY:
        raise ValueError("LLM API key is required")
    
    async def make_llm_call(call_id: int) -> dict[str, Any]:
        """Make a single call to the LLM API."""
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = await response.json()
                
                return {
                    "call_id": call_id,
                    "success": True,
                    "response": result["choices"][0]["message"]["content"],
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
                
        except Exception as e:
            logger.error(f"LLM call {call_id} failed: {str(e)}")
            return {
                "call_id": call_id,
                "success": False,
                "error": str(e),
                "response": None,
                "tokens_used": 0
            }
    
    # Create concurrent tasks
    tasks = [make_llm_call(i) for i in range(num_calls)]
    
    # Execute all calls concurrently
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Compile results
    successful_calls = [r for r in results if r["success"]]
    failed_calls = [r for r in results if not r["success"]]
    total_tokens = sum(r["tokens_used"] for r in results)
    
    logger.info(f"Completed {len(successful_calls)}/{num_calls} successful LLM calls")
    
    return {
        "results": results,
        "summary": {
            "total_calls": num_calls,
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "total_tokens_used": total_tokens
        },
        "responses": [r["response"] for r in successful_calls]
    }