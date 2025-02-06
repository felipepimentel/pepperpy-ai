"""Learning capability interface.

This module defines the base interface for learning capabilities,
which enable agents to learn from experience and improve over time.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")  # Training data type
M = TypeVar("M")  # Model type
P = TypeVar("P")  # Prediction type


class LearningType(str, Enum):
    """Type of learning."""

    SUPERVISED = "supervised"  # Learning from labeled examples
    UNSUPERVISED = "unsupervised"  # Learning patterns without labels
    REINFORCEMENT = "reinforcement"  # Learning from rewards/penalties
    TRANSFER = "transfer"  # Learning from related tasks
    META = "meta"  # Learning to learn
    ACTIVE = "active"  # Learning by asking questions


class LearningContext(BaseModel, Generic[T]):
    """Context for learning operations."""

    id: UUID = Field(default_factory=uuid4)
    type: LearningType
    data: T
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningResult(BaseModel, Generic[M]):
    """Result of a learning operation."""

    id: UUID = Field(default_factory=uuid4)
    context_id: UUID
    type: LearningType
    model: M
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictionContext(BaseModel):
    """Context for prediction operations."""

    id: UUID = Field(default_factory=uuid4)
    model_id: UUID
    input: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictionResult(BaseModel, Generic[P]):
    """Result of a prediction operation."""

    id: UUID = Field(default_factory=uuid4)
    context_id: UUID
    model_id: UUID
    prediction: P
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseLearning(ABC, Generic[T, M, P]):
    """Base interface for learning capabilities."""

    @abstractmethod
    async def train(
        self,
        context: LearningContext[T],
    ) -> LearningResult[M]:
        """Train a model on data.

        Args:
            context: Learning context

        Returns:
            Learning result

        Raises:
            LearningError: If training fails
        """
        raise NotImplementedError

    @abstractmethod
    async def predict(
        self,
        context: PredictionContext,
        model: M,
    ) -> PredictionResult[P]:
        """Make predictions using a trained model.

        Args:
            context: Prediction context
            model: Trained model to use

        Returns:
            Prediction result

        Raises:
            LearningError: If prediction fails
        """
        raise NotImplementedError

    @abstractmethod
    async def evaluate(
        self,
        context: LearningContext[T],
        model: M,
    ) -> dict[str, float]:
        """Evaluate model performance on data.

        Args:
            context: Learning context with evaluation data
            model: Model to evaluate

        Returns:
            Dictionary of evaluation metrics

        Raises:
            LearningError: If evaluation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        model: M,
        path: str,
    ) -> None:
        """Save model to disk.

        Args:
            model: Model to save
            path: Path to save model to

        Raises:
            LearningError: If saving fails
        """
        raise NotImplementedError

    @abstractmethod
    async def load(
        self,
        path: str,
    ) -> M:
        """Load model from disk.

        Args:
            path: Path to load model from

        Returns:
            Loaded model

        Raises:
            LearningError: If loading fails
        """
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        context: LearningContext[T],
        model: M,
    ) -> LearningResult[M]:
        """Update existing model with new data.

        Args:
            context: Learning context with new data
            model: Existing model to update

        Returns:
            Learning result with updated model

        Raises:
            LearningError: If update fails
        """
        raise NotImplementedError

    @abstractmethod
    async def reset(
        self,
        model: M,
    ) -> M:
        """Reset model to initial state.

        Args:
            model: Model to reset

        Returns:
            Reset model

        Raises:
            LearningError: If reset fails
        """
        raise NotImplementedError
