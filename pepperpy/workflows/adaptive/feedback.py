"""Feedback collection and processing for adaptive workflows."""

import abc
import enum
import logging
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pepperpy.core.base import BaseComponent

logger = logging.getLogger(__name__)


class FeedbackType(str, enum.Enum):
    """Types of feedback for adaptive workflows."""

    RATING = "rating"
    BINARY = "binary"
    TEXT = "text"
    STRUCTURED = "structured"


class Feedback:
    """Container for feedback data.

    This class provides a standardized way to represent feedback data
    for adaptive workflows.
    """

    def __init__(
        self,
        feedback_type: Union[str, FeedbackType],
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the feedback.

        Args:
            feedback_type: The type of feedback
            value: The feedback value
            metadata: Optional metadata for the feedback
        """
        # Normalize feedback type
        if isinstance(feedback_type, str):
            try:
                self.feedback_type = FeedbackType(feedback_type)
            except ValueError:
                raise ValueError(
                    f"Invalid feedback type: {feedback_type}. "
                    f"Valid types are: {', '.join([t.value for t in FeedbackType])}"
                )
        else:
            self.feedback_type = feedback_type

        self.value = value
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        """Get a string representation of the feedback.

        Returns:
            String representation
        """
        return f"Feedback(type={self.feedback_type.value}, value={self.value})"


@runtime_checkable
class FeedbackCollector(Protocol):
    """Protocol for feedback collectors.

    Feedback collectors are responsible for collecting feedback from users
    or other sources for adaptive workflows.
    """

    async def collect(
        self,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Feedback:
        """Collect feedback.

        Args:
            context: The context for feedback collection
            **kwargs: Additional parameters for feedback collection

        Returns:
            The collected feedback
        """
        ...


@runtime_checkable
class FeedbackProcessor(Protocol):
    """Protocol for feedback processors.

    Feedback processors are responsible for processing feedback and
    updating adaptive workflows based on the feedback.
    """

    async def process(
        self,
        feedback: Feedback,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process feedback.

        Args:
            feedback: The feedback to process
            context: The context for feedback processing
            **kwargs: Additional parameters for feedback processing

        Returns:
            The processing results
        """
        ...


class BaseFeedbackCollector(BaseComponent, abc.ABC):
    """Base class for feedback collectors.

    This class provides a base implementation for feedback collectors,
    with common functionality and validation.
    """

    def __init__(
        self,
        name: str,
        feedback_type: Union[str, FeedbackType],
        **kwargs: Any,
    ) -> None:
        """Initialize the feedback collector.

        Args:
            name: Name of the feedback collector
            feedback_type: The type of feedback to collect
            **kwargs: Additional parameters for the feedback collector
        """
        super().__init__()
        self._name = name

        # Normalize feedback type
        if isinstance(feedback_type, str):
            try:
                self.feedback_type = FeedbackType(feedback_type)
            except ValueError:
                raise ValueError(
                    f"Invalid feedback type: {feedback_type}. "
                    f"Valid types are: {', '.join([t.value for t in FeedbackType])}"
                )
        else:
            self.feedback_type = feedback_type

    @property
    def name(self) -> str:
        """Get the collector name.

        Returns:
            The collector name
        """
        return self._name

    async def collect(
        self,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Feedback:
        """Collect feedback.

        Args:
            context: The context for feedback collection
            **kwargs: Additional parameters for feedback collection

        Returns:
            The collected feedback
        """
        # Collect the feedback
        value, metadata = await self._collect(context, **kwargs)

        # Create and return the feedback
        return Feedback(
            feedback_type=self.feedback_type,
            value=value,
            metadata=metadata,
        )

    @abc.abstractmethod
    async def _collect(
        self,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> tuple[Any, Dict[str, Any]]:
        """Collect feedback.

        Args:
            context: The context for feedback collection
            **kwargs: Additional parameters for feedback collection

        Returns:
            A tuple of (feedback_value, metadata)
        """
        pass


class BaseFeedbackProcessor(BaseComponent, abc.ABC):
    """Base class for feedback processors.

    This class provides a base implementation for feedback processors,
    with common functionality and validation.
    """

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the feedback processor.

        Args:
            name: Name of the feedback processor
            **kwargs: Additional parameters for the feedback processor
        """
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        """Get the processor name.

        Returns:
            The processor name
        """
        return self._name

    async def process(
        self,
        feedback: Feedback,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process feedback.

        Args:
            feedback: The feedback to process
            context: The context for feedback processing
            **kwargs: Additional parameters for feedback processing

        Returns:
            The processing results
        """
        # Process the feedback
        results = await self._process(feedback, context, **kwargs)

        # Log the processing
        logger.info(
            "Processed feedback",
            extra={
                "processor": self.name,
                "feedback_type": feedback.feedback_type.value,
                "feedback_value": str(feedback.value),
                "results": results,
            },
        )

        return results

    @abc.abstractmethod
    async def _process(
        self,
        feedback: Feedback,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process feedback.

        Args:
            feedback: The feedback to process
            context: The context for feedback processing
            **kwargs: Additional parameters for feedback processing

        Returns:
            The processing results
        """
        pass


class RatingFeedbackCollector(BaseFeedbackCollector):
    """Collector for rating feedback.

    This collector collects rating feedback, such as 1-5 stars or 0-10 scores.
    """

    def __init__(
        self,
        name: str,
        min_rating: float = 1.0,
        max_rating: float = 5.0,
        **kwargs: Any,
    ) -> None:
        """Initialize the rating feedback collector.

        Args:
            name: Name of the feedback collector
            min_rating: Minimum rating value
            max_rating: Maximum rating value
            **kwargs: Additional parameters for the feedback collector
        """
        super().__init__(name=name, feedback_type=FeedbackType.RATING, **kwargs)
        self.min_rating = min_rating
        self.max_rating = max_rating

    async def _collect(
        self,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> tuple[float, Dict[str, Any]]:
        """Collect rating feedback.

        Args:
            context: The context for feedback collection
            **kwargs: Additional parameters for feedback collection
                - rating: The rating value
                - comments: Optional comments for the rating

        Returns:
            A tuple of (rating, metadata)
        """
        # Get the rating
        rating = kwargs.get("rating")
        if rating is None:
            raise ValueError("Rating is required")

        # Validate the rating
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid rating: {rating}. Must be a number.")

        if rating < self.min_rating or rating > self.max_rating:
            raise ValueError(
                f"Invalid rating: {rating}. "
                f"Must be between {self.min_rating} and {self.max_rating}."
            )

        # Get additional metadata
        comments = kwargs.get("comments", "")

        # Create and return the feedback
        return rating, {
            "min_rating": self.min_rating,
            "max_rating": self.max_rating,
            "comments": comments,
            "context": context,
        }


class SimpleFeedbackProcessor(BaseFeedbackProcessor):
    """Simple feedback processor.

    This processor processes feedback and updates a simple moving average
    of ratings or other numeric feedback.
    """

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the simple feedback processor.

        Args:
            name: Name of the feedback processor
            **kwargs: Additional parameters for the feedback processor
        """
        super().__init__(name=name, **kwargs)
        self.feedback_history: List[Feedback] = []
        self.average_rating: Optional[float] = None
        self.total_feedback = 0

    async def _process(
        self,
        feedback: Feedback,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process feedback.

        Args:
            feedback: The feedback to process
            context: The context for feedback processing
            **kwargs: Additional parameters for feedback processing
                - max_history: Maximum number of feedback items to keep

        Returns:
            The processing results
        """
        # Add the feedback to the history
        self.feedback_history.append(feedback)
        self.total_feedback += 1

        # Limit the history size
        max_history = kwargs.get("max_history", 100)
        if len(self.feedback_history) > max_history:
            self.feedback_history = self.feedback_history[-max_history:]

        # Update the average rating for numeric feedback
        if feedback.feedback_type in [FeedbackType.RATING, FeedbackType.BINARY]:
            try:
                value = float(feedback.value)
                if self.average_rating is None:
                    self.average_rating = value
                else:
                    # Simple moving average
                    self.average_rating = (
                        self.average_rating * (self.total_feedback - 1) + value
                    ) / self.total_feedback
            except (ValueError, TypeError):
                # Not a numeric value, skip
                pass

        # Return the processing results
        return {
            "total_feedback": self.total_feedback,
            "average_rating": self.average_rating,
            "history_size": len(self.feedback_history),
        }
