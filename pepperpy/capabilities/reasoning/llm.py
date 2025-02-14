"""Language model-based reasoning implementation.

This module provides a reasoning implementation that uses a language model
to perform various types of reasoning.
"""

from typing import Generic, TypeVar, cast
from uuid import uuid4

from pydantic import BaseModel, Field

from pepperpy.core.capability_errors import ReasoningError
from pepperpy.core.types import Message, MessageType
from pepperpy.monitoring.tracing import tracer
from pepperpy.providers.base import BaseProvider

from .base import BaseReasoning, ReasoningContext, ReasoningResult, ReasoningType

T = TypeVar("T", dict, str)  # Input type - must be dict or str
R = TypeVar("R")  # Result type
A = TypeVar("A")  # Action type - must be JSON-serializable


class LLMConfig(BaseModel):
    """Language model configuration."""

    provider: str = Field(
        description="Provider to use for language model",
    )
    model: str = Field(
        description="Model to use for reasoning",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for model sampling",
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Maximum tokens to generate",
    )
    stop_sequences: list[str] | None = Field(
        default=None,
        description="Optional sequences to stop generation",
    )


class LLMReasoning(BaseReasoning[T, A], Generic[T, A]):
    """Language model-based reasoning implementation."""

    def __init__(
        self,
        provider: BaseProvider,
        config: LLMConfig | None = None,
    ) -> None:
        """Initialize the reasoning implementation.

        Args:
            provider: Provider instance for language model
            config: Language model configuration

        Raises:
            ValueError: If config is invalid
            TypeError: If provider is not compatible with config

        """
        if not isinstance(provider, BaseProvider):
            raise TypeError("Provider must be an instance of BaseProvider")

        self.provider = provider

    async def reason(self, context: ReasoningContext[T]) -> ReasoningResult[A]:
        """Reason about input data.

        Args:
            context: Reasoning context containing input data and type

        Returns:
            ReasoningResult containing:
                action: Action to take
                confidence: Confidence in the action
                explanation: Explanation of the reasoning

        Raises:
            ReasoningError: If reasoning fails
            TypeError: If input_data is invalid type

        """
        with tracer.start_as_current_span("reason") as span:
            try:
                # Generate reasoning using language model
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="reasoner",
                            receiver=None,
                            content={"input": str(context.input)},
                        )
                    ],
                )

                # Parse response
                try:
                    result = response.content
                except KeyError as e:
                    raise ReasoningError(f"Invalid response format: {e}") from e

                # Extract and validate fields
                action = cast(A, result.get("action"))
                confidence = float(result.get("confidence", 0.0))
                explanation = str(result.get("explanation", ""))

                return ReasoningResult[A](
                    context_id=uuid4(),
                    type=context.type,
                    result=action,
                    confidence=confidence,
                    explanation=explanation,
                )

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error.type",
                    type(e).__name__,
                )
                span.set_attribute(
                    "error.message",
                    str(e),
                )
                if isinstance(e, TypeError | ValueError | ReasoningError):
                    raise
                raise ReasoningError(f"Reasoning failed: {e}") from e

    async def validate(self, result: ReasoningResult[A]) -> bool:
        """Validate a reasoning result.

        Args:
            result: Result to validate

        Returns:
            True if result is valid, False otherwise

        Raises:
            ReasoningError: If validation fails

        """
        with tracer.start_as_current_span("validate") as span:
            try:
                # Generate validation prompt
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="reasoner",
                            receiver=None,
                            content={
                                "result": result.model_dump(),
                            },
                        )
                    ],
                )

                # Parse response
                try:
                    validation_result = response.content
                    return bool(validation_result.get("valid", False))
                except KeyError as e:
                    raise ReasoningError(f"Invalid validation response: {e}") from e

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error.type",
                    type(e).__name__,
                )
                span.set_attribute(
                    "error.message",
                    str(e),
                )
                raise ReasoningError(f"Validation failed: {e}") from e

    async def explain(
        self,
        result: ReasoningResult[A],
    ) -> str:
        """Get detailed explanation of reasoning result.

        Args:
            result: Reasoning result to explain

        Returns:
            Detailed explanation

        Raises:
            ReasoningError: If explanation fails

        """
        try:
            # If result has explanation, use it
            if result.explanation:
                return result.explanation

            # Otherwise, generate explanation from result
            if not isinstance(result.result, dict):
                return str(result.result)

            # Build explanation based on reasoning type
            if result.type == ReasoningType.DEDUCTIVE:
                conclusions = result.result.get("conclusions", [])
                return (
                    "Through deductive reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + "\n".join(f"- {c}" for c in conclusions)
                )

            if result.type == ReasoningType.INDUCTIVE:
                patterns = result.result.get("generalizations", [])
                predictions = result.result.get("predictions", [])
                return (
                    "Through inductive reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + "Patterns identified:\n"
                    + "\n".join(f"- {p}" for p in patterns)
                    + "\n\nPredictions:\n"
                    + "\n".join(f"- {p}" for p in predictions)
                )

            if result.type == ReasoningType.ABDUCTIVE:
                explanation = result.result.get("best_explanation", "")
                evidence = result.result.get("evidence", [])
                return (
                    "Through abductive reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + f"Best explanation: {explanation}\n\n"
                    + "Supporting evidence:\n"
                    + "\n".join(f"- {e}" for e in evidence)
                )

            if result.type == ReasoningType.ANALOGICAL:
                similarities = result.result.get("similarities", [])
                differences = result.result.get("differences", [])
                insights = result.result.get("insights", [])
                return (
                    "Through analogical reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + "Similarities:\n"
                    + "\n".join(f"- {s}" for s in similarities)
                    + "\n\nDifferences:\n"
                    + "\n".join(f"- {d}" for d in differences)
                    + "\n\nInsights:\n"
                    + "\n".join(f"- {i}" for i in insights)
                )

            if result.type == ReasoningType.CAUSAL:
                causes = result.result.get("causes", [])
                effects = result.result.get("effects", [])
                relationships = result.result.get("relationships", [])
                return (
                    "Through causal reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + "Causes:\n"
                    + "\n".join(f"- {c}" for c in causes)
                    + "\n\nEffects:\n"
                    + "\n".join(f"- {e}" for e in effects)
                    + "\n\nRelationships:\n"
                    + "\n".join(f"- {r}" for r in relationships)
                )

            if result.type == ReasoningType.COUNTERFACTUAL:
                alternatives = result.result.get("alternatives", [])
                implications = result.result.get("implications", [])
                insights = result.result.get("insights", [])
                return (
                    "Through counterfactual reasoning "
                    f"(confidence: {result.confidence:.2f}):\n\n"
                    + "Alternatives considered:\n"
                    + "\n".join(f"- {a}" for a in alternatives)
                    + "\n\nImplications:\n"
                    + "\n".join(f"- {i}" for i in implications)
                    + "\n\nInsights:\n"
                    + "\n".join(f"- {i}" for i in insights)
                )

            return str(result.result)

        except Exception as e:
            raise ReasoningError(f"Failed to explain result: {e!s}") from e
