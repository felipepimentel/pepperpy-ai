"""Learning factory.

This module provides a factory for creating learning instances
based on configuration.
"""

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from pepperpy.providers.base import BaseProvider

from .base import BaseLearning
from .llm import LLMConfig, LLMLearning

T = TypeVar("T")  # Training data type
M = TypeVar("M", bound=dict[str, Any])  # Model type (dictionary)
P = TypeVar("P")  # Prediction type


class LearningImplType(str, Enum):
    """Type of learning implementation."""

    LLM = "llm"  # Language model-based learning


class LearningConfig(BaseModel):
    """Learning configuration."""

    type: LearningImplType = Field(
        default=LearningImplType.LLM,
        description="Type of learning implementation to use",
    )
    llm: LLMConfig | None = Field(
        default=None,
        description="Language model learning configuration",
    )


class LearningFactory(Generic[T, M, P]):
    """Factory for creating learning instances."""

    def __init__(self, config: LearningConfig | None = None) -> None:
        """Initialize the learning factory.

        Args:
            config: Optional learning configuration
        """
        self._config = config or LearningConfig()

    def create(self, provider: BaseProvider) -> BaseLearning[T, M, P]:
        """Create a learning instance.

        Args:
            provider: Provider instance for language model

        Returns:
            Learning instance

        Raises:
            ValueError: If configuration is invalid
        """
        if self._config.type == LearningImplType.LLM:
            if not self._config.llm:
                raise ValueError(
                    "Language model configuration is required for LLM learning"
                )
            return LLMLearning[T, M, P](self._config.llm, provider)

        raise ValueError(f"Unknown learning type: {self._config.type}")
