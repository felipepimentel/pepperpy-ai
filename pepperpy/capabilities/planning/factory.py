"""Planning factory.

This module provides a factory for creating planning instances
based on configuration.
"""

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from pepperpy.providers.base import BaseProvider

from .base import BasePlanning
from .llm import LLMConfig, LLMPlanning

# Type variables for generic implementations
T = TypeVar("T", dict, str)  # Task/State type - must be dict or str
A = TypeVar("A")  # Action type


class PlanningImplType(str, Enum):
    """Type of planning implementation."""

    LLM = "llm"  # Language model-based planning


class PlanningConfig(BaseModel):
    """Planning configuration."""

    type: PlanningImplType = Field(
        default=PlanningImplType.LLM,
        description="Type of planning implementation to use",
    )
    llm: LLMConfig | None = Field(
        default=None,
        description="Language model configuration (required if type is llm)",
    )


class PlanningFactory(Generic[T, A]):
    """Factory for creating planning instances.

    Type Parameters:
        T: Task/State type - must be dict or str for LLM planning
        A: Action type
    """

    def __init__(self, config: PlanningConfig | None = None):
        """Initialize the planning factory.

        Args:
            config: Optional planning configuration
        """
        self._config = config or PlanningConfig()

    def create(self, provider: BaseProvider) -> BasePlanning[T, T, A]:
        """Create a planning instance.

        Args:
            provider: Provider instance for language model

        Returns:
            Planning instance

        Raises:
            ValueError: If configuration is invalid
        """
        if self._config.type == PlanningImplType.LLM:
            if not self._config.llm:
                raise ValueError(
                    "Language model configuration is required for LLM planning"
                )
            # Create LLMPlanning with correct type parameters
            # LLMPlanning uses T for both input and state types
            planner: BasePlanning[T, T, A] = LLMPlanning[T, A](
                config=self._config.llm,
                provider=provider,
            )
            return planner

        raise ValueError(f"Unknown planning type: {self._config.type}")


def create_planning(
    planning_type: str,
    config: dict[str, Any],
    provider: BaseProvider,
) -> BasePlanning[T, T, A]:
    """Create a planning capability.

    Args:
        planning_type: Type of planning to create
        config: Configuration for the planner
        provider: Provider instance for language model

    Returns:
        Planning capability instance

    Raises:
        ValueError: If planning type is not supported
    """
    if planning_type == "llm":
        # LLMPlanning uses T for both input and state types
        planner: BasePlanning[T, T, A] = LLMPlanning[T, A](
            config=LLMConfig(**config),
            provider=provider,
        )
        return planner
    raise ValueError(f"Unsupported planning type: {planning_type}")
