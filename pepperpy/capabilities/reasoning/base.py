"""Reasoning capability interface.

This module defines the base interface for reasoning capabilities,
which enable agents to perform logical reasoning and inference.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type


class ReasoningType(str, Enum):
    """Type of reasoning."""

    DEDUCTIVE = "deductive"  # Drawing conclusions from premises
    INDUCTIVE = "inductive"  # Generalizing from examples
    ABDUCTIVE = "abductive"  # Finding best explanation
    ANALOGICAL = "analogical"  # Comparing similar cases
    CAUSAL = "causal"  # Identifying cause and effect
    COUNTERFACTUAL = "counterfactual"  # Considering alternatives


class ReasoningContext(BaseModel, Generic[T]):
    """Context for reasoning operations."""

    id: UUID = Field(default_factory=uuid4)
    type: ReasoningType
    input: T
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReasoningResult(BaseModel, Generic[R]):
    """Result of a reasoning operation."""

    id: UUID = Field(default_factory=uuid4)
    context_id: UUID
    type: ReasoningType
    result: R
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseReasoning(ABC, Generic[T, R]):
    """Base interface for reasoning capabilities."""

    @abstractmethod
    async def reason(
        self,
        context: ReasoningContext[T],
    ) -> ReasoningResult[R]:
        """Perform reasoning operation.

        Args:
            context: Reasoning context

        Returns:
            Reasoning result

        Raises:
            ReasoningError: If reasoning fails
        """
        raise NotImplementedError

    @abstractmethod
    async def explain(
        self,
        result: ReasoningResult[R],
    ) -> str:
        """Get detailed explanation of reasoning result.

        Args:
            result: Reasoning result to explain

        Returns:
            Detailed explanation

        Raises:
            ReasoningError: If explanation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def validate(
        self,
        result: ReasoningResult[R],
    ) -> bool:
        """Validate reasoning result.

        Args:
            result: Reasoning result to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ReasoningError: If validation fails
        """
        raise NotImplementedError
