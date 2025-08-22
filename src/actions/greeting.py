"""
My demo feature action implementation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def greeting_action(
    person_being_greeted: str,
) -> str:
    """
    Greets the user.
    
    Args:
        person_being_greeted: The name of the person to greet.

    Returns:
        Result of the action
    """
    logger.info("My feature action called")
    
    # Your implementation here
    result = f"---- Hello {person_being_greeted}! ----"
    
    logger.info("My feature action completed")
    return result
