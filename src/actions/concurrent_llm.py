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
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


async def evaluation_sub_agent_action(
    context: str,
    num_calls: int = 3,
    system_prompt: str = "You are a helpful assistant.",
) -> list[dict[str, str]]:
    """
    Make concurrent calls to an LLM subagent with given context and system prompt.
    
    Args:
        context: The context to send to the subagent
        num_calls: Number of concurrent calls to make (default: 3)
        system_prompt: Intructions that you want to the subagent to apply to the context.
    
    Returns:
        List of results, as dictionary with the response key containing the response of the subagent call
        Each item in the list is a response from a single subagent call
    """
    logger.info(f"Starting {num_calls} concurrent LLM calls")
    
    if not LLM_API_KEY:
        raise ValueError("LLM API key is required")
    
    if not LLM_BASE_URL:
        raise ValueError("LLM_BASE_URL is required")
    
    if not LLM_MODEL:
        raise ValueError("LLM_MODEL is required")
    
    async def make_llm_call(call_id: int) -> dict[str, Any]:
        """Make a single call to the LLM API."""
        
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ]
        }
        
        # Add temperature only for models that support it
        # gpt-5-nano only supports default temperature (1.0)
        if LLM_MODEL and not LLM_MODEL.startswith('gpt-5'):
            payload["temperature"] = LLM_TEMPERATURE
        
        request_url = f"{LLM_BASE_URL}/chat/completions"
        
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    request_url,
                    headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                    json=payload
                )
                
                if response.status_code != 200:
                    response_text = response.text
                    logger.error(f"LLM call {call_id} - HTTP {response.status_code}: {response_text}")
                
                response.raise_for_status()
                result = response.json()
                
                
                if not isinstance(result, dict):
                    raise ValueError(f"Expected dict response, got {type(result)}")
                
                choices = result.get('choices', [])
                
                if not choices:
                    raise ValueError("No choices in response")
                
                message_content = choices[0].get('message', {}).get('content', '')
                usage = result.get('usage', {})
                tokens_used = usage.get('total_tokens', 0) if isinstance(usage, dict) else 0
                
                return {
                    "call_id": call_id,
                    "success": True,
                    "response": message_content,
                    "tokens_used": tokens_used
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
            try:
                error_detail = e.response.text
                logger.error(f"LLM call {call_id} - {error_msg}: {error_detail}")
                error_msg += f" - {error_detail}"
            except Exception:
                logger.error(f"LLM call {call_id} - {error_msg}")
            
            return {
                "call_id": call_id,
                "success": False,
                "error": error_msg,
                "response": None,
                "tokens_used": 0
            }
        except httpx.RequestError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(f"LLM call {call_id} - {error_msg}")
            return {
                "call_id": call_id,
                "success": False,
                "error": error_msg,
                "response": None,
                "tokens_used": 0
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"LLM call {call_id} - {error_msg}")
            return {
                "call_id": call_id,
                "success": False,
                "error": error_msg,
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
    
    logger.info(f"Completed {len(successful_calls)}/{num_calls} successful LLM calls, total tokens: {total_tokens}")
    
    if failed_calls:
        logger.warning(f"{len(failed_calls)} calls failed")
    
    return results