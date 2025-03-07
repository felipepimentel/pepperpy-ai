"""Adaptive learning for workflows."""

import logging
from typing import Any, Dict, Optional, Type

from pepperpy.core.base import BaseComponent
from pepperpy.workflows.adaptive.feedback import (
    Feedback,
    FeedbackCollector,
    FeedbackProcessor,
)

logger = logging.getLogger(__name__)

# Registry of adaptive workflow types
_ADAPTIVE_WORKFLOW_REGISTRY: Dict[str, Type["AdaptiveWorkflow"]] = {}


def register_adaptive_workflow(
    workflow_type: str,
) -> callable:
    """Register an adaptive workflow type.

    Args:
        workflow_type: The type of workflow to register

    Returns:
        A decorator function

    Examples:
        >>> @register_adaptive_workflow("summarization")
        >>> class SummarizationWorkflow(AdaptiveWorkflow):
        ...     pass
    """

    def decorator(cls: Type["AdaptiveWorkflow"]) -> Type["AdaptiveWorkflow"]:
        """Register the workflow class.

        Args:
            cls: The workflow class to register

        Returns:
            The registered workflow class

        Raises:
            ValueError: If a workflow with the same type is already registered
        """
        if workflow_type in _ADAPTIVE_WORKFLOW_REGISTRY:
            raise ValueError(
                f"An adaptive workflow for type '{workflow_type}' "
                f"is already registered: {_ADAPTIVE_WORKFLOW_REGISTRY[workflow_type].__name__}"
            )

        _ADAPTIVE_WORKFLOW_REGISTRY[workflow_type] = cls

        logger.info(
            "Registered adaptive workflow",
            extra={
                "workflow_type": workflow_type,
                "workflow_class": cls.__name__,
            },
        )

        return cls

    return decorator


def create_adaptive_workflow(
    workflow_type: str,
    name: Optional[str] = None,
    **kwargs: Any,
) -> "AdaptiveWorkflow":
    """Create an adaptive workflow.

    Args:
        workflow_type: The type of workflow to create
        name: Optional name for the workflow
        **kwargs: Additional parameters for the workflow

    Returns:
        An instance of the requested workflow

    Raises:
        ValueError: If no workflow is registered for the specified type

    Examples:
        >>> workflow = create_adaptive_workflow("summarization")
        >>> result = workflow.process(document)
        >>> workflow.learn_from_feedback(user_rating=4)
    """
    # Check if a workflow is registered
    if workflow_type not in _ADAPTIVE_WORKFLOW_REGISTRY:
        raise ValueError(
            f"No adaptive workflow registered for type '{workflow_type}'. "
            f"Available types: {', '.join(_ADAPTIVE_WORKFLOW_REGISTRY.keys())}"
        )

    # Get the workflow class
    workflow_class = _ADAPTIVE_WORKFLOW_REGISTRY[workflow_type]

    # Create and return the workflow
    return workflow_class(
        name=name or f"{workflow_type}_workflow",
        **kwargs,
    )


class AdaptiveWorkflow(BaseComponent):
    """Base class for adaptive workflows.

    Adaptive workflows learn from feedback and adapt their behavior
    based on usage patterns and user preferences.
    """

    def __init__(
        self,
        name: str,
        feedback_collector: Optional[FeedbackCollector] = None,
        feedback_processor: Optional[FeedbackProcessor] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the adaptive workflow.

        Args:
            name: Name of the workflow
            feedback_collector: Optional feedback collector
            feedback_processor: Optional feedback processor
            **kwargs: Additional parameters for the workflow
        """
        super().__init__()
        self._name = name
        self.workflow = self._create_workflow(**kwargs)
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_context: Optional[Dict[str, Any]] = None

        # Set up feedback components
        self.feedback_collector = (
            feedback_collector or self._create_feedback_collector()
        )
        self.feedback_processor = (
            feedback_processor or self._create_feedback_processor()
        )

    @property
    def name(self) -> str:
        """Get the workflow name.

        Returns:
            The workflow name
        """
        return self._name

    def _create_workflow(self, **kwargs: Any) -> Any:
        """Create the underlying workflow.

        Args:
            **kwargs: Additional parameters for the workflow

        Returns:
            The created workflow
        """
        # This should be overridden by subclasses
        return {"name": self.name}

    def _create_feedback_collector(self) -> FeedbackCollector:
        """Create a default feedback collector.

        Returns:
            A feedback collector
        """

        # In a real implementation, this would create a proper feedback collector
        # For now, we'll create a simple mock
        class MockFeedbackCollector:
            async def collect(self, context: Dict[str, Any], **kwargs: Any) -> Feedback:
                rating = kwargs.get("user_rating", 5)
                return Feedback("rating", rating, {"context": context})

        return MockFeedbackCollector()

    def _create_feedback_processor(self) -> FeedbackProcessor:
        """Create a default feedback processor.

        Returns:
            A feedback processor
        """

        # In a real implementation, this would create a proper feedback processor
        # For now, we'll create a simple mock
        class MockFeedbackProcessor:
            async def process(
                self,
                feedback: Feedback,
                context: Dict[str, Any],
                **kwargs: Any,
            ) -> Dict[str, Any]:
                return {
                    "status": "success",
                    "feedback_type": feedback.feedback_type.value,
                    "feedback_value": feedback.value,
                }

        return MockFeedbackProcessor()

    async def initialize(self) -> None:
        """Initialize the workflow."""
        pass

    async def process(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process input data with the workflow.

        Args:
            input_data: The input data to process
            context: Optional context for processing
            **kwargs: Additional parameters for processing

        Returns:
            The processing results
        """
        # Create the processing context
        processing_context = context or {}
        processing_context.update({
            "workflow_name": self.name,
            "input_type": type(input_data).__name__,
        })

        # Process the input
        # In a real implementation, this would use the workflow's run method
        result = {
            "status": "success",
            "output": f"Processed {type(input_data).__name__}",
        }

        # Store the result and context for feedback
        self.last_result = result
        self.last_context = processing_context

        return result

    async def learn_from_feedback(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Learn from feedback.

        Args:
            **kwargs: Feedback parameters
                - user_rating: Optional user rating (1-5)
                - comments: Optional user comments
                - feedback_data: Optional explicit feedback data

        Returns:
            The learning results

        Raises:
            ValueError: If no previous processing result is available
        """
        # Check if we have a previous result
        if self.last_result is None or self.last_context is None:
            raise ValueError(
                "No previous processing result available for feedback. "
                "Call process() first."
            )

        # Create the feedback context
        feedback_context = {
            "workflow_name": self.name,
            "last_result": self.last_result,
            "last_context": self.last_context,
        }

        # Collect feedback
        feedback = await self.feedback_collector.collect(
            context=feedback_context,
            **kwargs,
        )

        # Process feedback
        results = await self.feedback_processor.process(
            feedback=feedback,
            context=feedback_context,
            **kwargs,
        )

        # Apply learning
        await self._apply_learning(feedback, results, **kwargs)

        return results

    async def _apply_learning(
        self,
        feedback: Feedback,
        results: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Apply learning from feedback.

        Args:
            feedback: The feedback to learn from
            results: The feedback processing results
            **kwargs: Additional parameters for learning
        """
        # This should be overridden by subclasses
        logger.info(
            "Learning from feedback",
            extra={
                "workflow_name": self.name,
                "feedback_type": feedback.feedback_type.value,
                "feedback_value": str(feedback.value),
                "results": results,
            },
        )


@register_adaptive_workflow("summarization")
class SummarizationWorkflow(AdaptiveWorkflow):
    """Adaptive workflow for text summarization.

    This workflow summarizes text and adapts based on user feedback
    to improve summarization quality.
    """

    def _create_workflow(self, **kwargs: Any) -> Any:
        """Create the summarization workflow.

        Args:
            **kwargs: Additional parameters for the workflow
                - model: Optional model to use for summarization
                - max_length: Optional maximum length of the summary

        Returns:
            The created workflow
        """
        # Get workflow parameters
        model = kwargs.get("model", "default")
        max_length = kwargs.get("max_length", 200)

        # Create the workflow
        workflow = {"name": self.name, "model": model, "max_length": max_length}

        # In a real implementation, this would create a proper workflow
        # For now, we'll create a simple dictionary

        return workflow

    async def process(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process input data with the summarization workflow.

        Args:
            input_data: The input data to process
            context: Optional context for processing
            **kwargs: Additional parameters for processing

        Returns:
            The processing results
        """
        # Create the processing context
        processing_context = context or {}
        processing_context.update({
            "workflow_name": self.name,
            "input_type": type(input_data).__name__,
        })

        # Process the input
        # In a real implementation, this would use a summarization model
        result = {
            "status": "success",
            "summary": f"Summary of {type(input_data).__name__}",
            "model": self.workflow.get("model", "default"),
            "max_length": self.workflow.get("max_length", 200),
        }

        # Store the result and context for feedback
        self.last_result = result
        self.last_context = processing_context

        return result

    async def _apply_learning(
        self,
        feedback: Feedback,
        results: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Apply learning from feedback for summarization.

        Args:
            feedback: The feedback to learn from
            results: The feedback processing results
            **kwargs: Additional parameters for learning
        """
        # In a real implementation, this would adjust the summarization parameters
        # based on the feedback

        # For now, we'll just log the learning
        logger.info(
            "Learning from summarization feedback",
            extra={
                "workflow_name": self.name,
                "feedback_type": feedback.feedback_type.value,
                "feedback_value": str(feedback.value),
                "average_rating": results.get("average_rating"),
            },
        )
