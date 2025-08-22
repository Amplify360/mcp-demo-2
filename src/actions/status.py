"""
Status action implementation - demonstrates action with no dependencies.
"""

import logging

logger = logging.getLogger(__name__)


async def status_action() -> dict:
    """
    Get server status information.

    Returns:
        Status information dictionary
    """
    logger.info("Status action called")
    return {
        "status": "ok",
        "message": "MCP SSE Server is running",
        "version": "1.0.0"
    }