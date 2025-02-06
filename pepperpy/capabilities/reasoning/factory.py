"""Reasoning factory.

This module provides a factory for creating reasoning instances
based on configuration.
"""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from pepperpy.providers.base import BaseProvider

from .base import BaseReasoning
from .llm import LLMConfig, LLMReasoning

T = TypeVar("T", dict, str)  # Input type must be dict or str
R = TypeVar("R")  # Result type


class ReasoningType(str, Enum):
    """Type of reasoning implementation."""

    LLM = "llm"  # Language model-based reasoning


class ReasoningConfig(BaseModel):
    """Reasoning configuration."""

    type: ReasoningType = Field(
        default=ReasoningType.LLM,
        description="Type of reasoning implementation to use",
    )
    llm: LLMConfig | None = Field(
        default=None,
        description="Language model configuration (required if type is llm)",
    )


class ReasoningFactory(Generic[T, R]):
    """Factory for creating reasoning instances."""

    def __init__(self, config: ReasoningConfig | None = None):
        """Initialize the reasoning factory.

        Args:
            config: Optional reasoning configuration
        """
        self._config = config or ReasoningConfig()

    def create(self, provider: BaseProvider) -> BaseReasoning[T, R]:
        """Create a reasoning instance.

        Args:
            provider: Provider instance for language model

        Returns:
            Reasoning instance

        Raises:
            ValueError: If configuration is invalid
        """
        if self._config.type == ReasoningType.LLM:
            if not self._config.llm:
                raise ValueError(
                    "Language model configuration is required for LLM reasoning"
                )
            return LLMReasoning[T, R](provider)

        raise ValueError(f"Unknown reasoning type: {self._config.type}")
