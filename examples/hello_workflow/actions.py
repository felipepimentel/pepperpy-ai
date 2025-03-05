"""Example workflow actions.

This module provides example workflow actions to demonstrate
the workflow system's capabilities.
"""

import asyncio
import random
from typing import Dict, List

from pepperpy.core.common.monitoring.logging import get_logger
from pepperpy.core.common.workflows.actions import (
    Action,
    ActionContext,
    action_registry,
)


class HelloWorldAction(Action):
    """Simple action that returns a greeting message."""

    async def execute(self, context: ActionContext) -> Dict[str, str]:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Dictionary with greeting message

        """
        name = context.inputs.get("name", "World")
        return {"message": f"Hello, {name}!"}


class DelayAction(Action):
    """Action that simulates work by sleeping."""

    async def execute(self, context: ActionContext) -> None:
        """Execute the action.

        Args:
            context: Action execution context

        """
        delay = float(context.inputs.get("delay", 1.0))
        await asyncio.sleep(delay)


class RandomNumberAction(Action):
    """Action that generates random numbers."""

    async def execute(self, context: ActionContext) -> Dict[str, float]:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Dictionary with random number

        """
        min_val = float(context.inputs.get("min", 0.0))
        max_val = float(context.inputs.get("max", 1.0))
        return {"random_value": random.uniform(min_val, max_val)}


class ListProcessorAction(Action):
    """Action that processes a list of items."""

    async def execute(self, context: ActionContext) -> Dict[str, List[str]]:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Dictionary with processed items

        """
        items = context.inputs.get("items", [])
        prefix = context.inputs.get("prefix", "")
        processed = [f"{prefix}{item}" for item in items]
        return {"processed_items": processed}


def register_example_actions() -> None:
    """Register example actions with the action registry."""
    logger = get_logger(__name__)
    logger.info("Registering example actions")

    # Register class-based actions
    action_registry.register_action("hello_world", HelloWorldAction())
    action_registry.register_action("delay", DelayAction())
    action_registry.register_action("random_number", RandomNumberAction())
    action_registry.register_action("list_processor", ListProcessorAction())

    # Register a function-based action
    async def uppercase_text(context: ActionContext) -> Dict[str, str]:
        text = context.inputs.get("text", "")
        return {"uppercase": text.upper()}

    action_registry.register_function("uppercase", uppercase_text)

    logger.info("Example actions registered")
