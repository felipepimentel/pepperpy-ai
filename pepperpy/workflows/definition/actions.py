"""Workflow action registry implementation.

This module provides the action registry that manages workflow step actions,
including registration, lookup, and execution of actions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from pepperpy.core.common.lifecycle import Lifecycle
from pepperpy.core.common.monitoring.logging import get_logger

# Type variable for action results
T = TypeVar("T")


@dataclass
class ActionContext:
    """Context passed to workflow actions during execution."""

    workflow_id: str
    step_name: str
    inputs: Dict[str, Any]
    variables: Dict[str, Any]


class Action(ABC):
    """Base class for workflow actions.

    Actions represent the actual work performed by workflow steps.
    They can be synchronous or asynchronous functions that take
    an action context and return a result.
    """

    @abstractmethod
    async def execute(self, context: ActionContext) -> Any:
        """Execute the action.

        Args:
            context: Action execution context

        Returns:
            Action result

        Raises:
            Exception: If action execution fails

        """


class ActionRegistry(Lifecycle):
    """Registry for workflow actions.

    This class manages the registration and lookup of workflow actions,
    providing a central point for action execution.
    """

    def __init__(self) -> None:
        """Initialize the action registry."""
        super().__init__()
        self._actions: Dict[str, Action] = {}
        self._logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the action registry."""
        self._logger.info("Initializing action registry")

    async def cleanup(self) -> None:
        """Clean up action registry resources."""
        self._logger.info("Cleaning up action registry")
        self._actions.clear()

    def register_action(self, name: str, action: Action) -> None:
        """Register a new action.

        Args:
            name: Action name
            action: Action implementation

        Raises:
            ValueError: If action name already exists

        """
        if name in self._actions:
            raise ValueError(f"Action {name} already registered")

        self._actions[name] = action
        self._logger.info("Registered action", action_name=name)

    def register_function(
        self,
        name: str,
        func: Callable[[ActionContext], Any],
    ) -> None:
        """Register a function as an action.

        This is a convenience method that wraps a function in an Action class.

        Args:
            name: Action name
            func: Function to register

        Raises:
            ValueError: If action name already exists

        """

        class FunctionAction(Action):
            async def execute(self, context: ActionContext) -> Any:
                return await func(context)

        self.register_action(name, FunctionAction())

    def get_action(self, name: str) -> Optional[Action]:
        """Get an action by name.

        Args:
            name: Action name

        Returns:
            Action if found, None otherwise

        """
        return self._actions.get(name)

    async def execute_action(
        self,
        name: str,
        context: ActionContext,
    ) -> Any:
        """Execute an action by name.

        Args:
            name: Action name
            context: Action execution context

        Returns:
            Action result

        Raises:
            ValueError: If action not found
            Exception: If action execution fails

        """
        action = self.get_action(name)
        if not action:
            raise ValueError(f"Action {name} not found")

        self._logger.info(
            "Executing action",
            action_name=name,
            workflow_id=context.workflow_id,
            step_name=context.step_name,
        )

        try:
            result = await action.execute(context)
            self._logger.info(
                "Action completed",
                action_name=name,
                workflow_id=context.workflow_id,
                step_name=context.step_name,
            )
            return result

        except Exception as e:
            self._logger.error(
                "Action failed",
                action_name=name,
                workflow_id=context.workflow_id,
                step_name=context.step_name,
                error=str(e),
            )
            raise


# Global action registry instance
action_registry = ActionRegistry()
