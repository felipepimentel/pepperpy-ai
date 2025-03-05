"""Example workflow actions.

This module provides example workflow actions to demonstrate
the workflow system's capabilities.
"""

import asyncio
import random
from typing import Dict, List

from pepperpy.core.common.utils.logging import get_logger
from pepperpy.workflows.actions import (
    Action,
    ActionContext,
    action_registry,
)

logger = get_logger(__name__)


class HelloWorldAction(Action):
    """Simple action that returns a greeting message."""

    async def execute(self, context: ActionContext) -> Dict[str, str]:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Dictionary with greeting message

        """
        logger.info("Executing HelloWorldAction")
        return {"message": "Hello, World!"}


class RandomDelayAction(Action):
    """Action that introduces a random delay.

    This action demonstrates how to implement an action that
    performs asynchronous operations.
    """

    async def execute(self, context: ActionContext) -> Dict[str, float]:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Dictionary with delay information

        """
        min_delay = context.parameters.get("min_delay", 0.1)
        max_delay = context.parameters.get("max_delay", 1.0)

        delay = random.uniform(min_delay, max_delay)
        logger.info(f"Delaying for {delay:.2f} seconds")

        await asyncio.sleep(delay)

        return {
            "delay": delay,
            "min_delay": min_delay,
            "max_delay": max_delay,
        }


# Register actions
action_registry.register("hello_world", HelloWorldAction)
action_registry.register("random_delay", RandomDelayAction)
