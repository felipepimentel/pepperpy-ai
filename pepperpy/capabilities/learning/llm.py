"""Language model-based learning implementation.

This module provides a learning implementation that uses a language model
for few-shot learning and pattern recognition.
"""

import json
import os
from collections.abc import AsyncGenerator
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.capabilities.learning.base import (
    BaseLearning,
    LearningContext,
    LearningResult,
    LearningType,
    PredictionContext,
    PredictionResult,
)
from pepperpy.core.errors import LearningError
from pepperpy.providers.base import BaseProvider

T = TypeVar("T")  # Input/output data type
M = TypeVar("M", bound=dict[str, Any])  # Model type
P = TypeVar("P")  # Prediction type


class LLMConfig(BaseModel):
    """Language model configuration."""

    provider: str = Field(
        description="Provider to use for language model",
    )
    model: str = Field(
        description="Model to use for learning",
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
        description="Stop sequences for generation",
    )


class LLMLearning(BaseLearning[T, M, P], Generic[T, M, P]):
    """Language model-based learning implementation."""

    def __init__(
        self,
        config: LLMConfig,
        provider: BaseProvider,
    ) -> None:
        """Initialize language model learning.

        Args:
            config: Learning configuration
            provider: Language model provider
        """
        self._config = config
        self._provider = provider

    async def _get_response_text(
        self, response: str | AsyncGenerator[str, None]
    ) -> str:
        """Get text from response.

        Args:
            response: Response from provider

        Returns:
            Response text
        """
        if isinstance(response, AsyncGenerator):
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            return "".join(chunks)
        return response

    def _make_prompt(
        self,
        context: LearningContext[T] | PredictionContext,
        examples: list[dict[str, Any]] | None = None,
    ) -> str:
        """Make prompt for language model.

        Args:
            context: Learning or prediction context
            examples: Optional list of examples for few-shot learning

        Returns:
            Prompt string
        """
        # Convert input to string representation
        if isinstance(context, LearningContext):
            input_str = (
                context.data
                if isinstance(context.data, str)
                else json.dumps(context.data, indent=2)
            )
        else:
            input_str = (
                context.input
                if isinstance(context.input, str)
                else json.dumps(context.input, indent=2)
            )

        # Build prompt based on learning type
        if isinstance(context, LearningContext):
            if context.type == LearningType.SUPERVISED:
                return f"""Given the following labeled examples:

{input_str}

Learn the patterns and relationships between inputs and outputs.
Create a model that can make predictions for new inputs.

Provide your learning results in JSON format:
{{
    "patterns": ["List of identified patterns"],
    "rules": ["List of learned rules"],
    "examples": {{"input": "example", "output": "example"}},
    "metrics": {{"accuracy": 0.0-1.0}}
}}"""

            if context.type == LearningType.UNSUPERVISED:
                return f"""Given the following unlabeled examples:

{input_str}

Identify patterns, clusters, and relationships in the data.
Create a model that captures the underlying structure.

Provide your learning results in JSON format:
{{
    "patterns": ["List of identified patterns"],
    "clusters": ["List of discovered clusters"],
    "relationships": ["List of relationships found"],
    "metrics": {{"cohesion": 0.0-1.0}}
}}"""

            if context.type == LearningType.REINFORCEMENT:
                return f"""Given the following experience data:

{input_str}

Learn optimal actions based on rewards and penalties.
Create a model that maximizes expected rewards.

Provide your learning results in JSON format:
{{
    "policy": ["List of learned action rules"],
    "values": {{"state": "value"}},
    "metrics": {{"reward": 0.0-1.0}}
}}"""

            if context.type == LearningType.TRANSFER:
                return f"""Given the following source task examples:

{input_str}

Transfer knowledge to improve learning on target task.
Create a model that leverages prior knowledge.

Provide your learning results in JSON format:
{{
    "knowledge": ["List of transferred concepts"],
    "adaptations": ["List of task-specific adaptations"],
    "metrics": {{"transfer": 0.0-1.0}}
}}"""

            if context.type == LearningType.META:
                return f"""Given the following learning experiences:

{input_str}

Learn strategies for improving learning efficiency.
Create a model that optimizes learning process.

Provide your learning results in JSON format:
{{
    "strategies": ["List of meta-learning strategies"],
    "optimizations": ["List of process improvements"],
    "metrics": {{"efficiency": 0.0-1.0}}
}}"""

            if context.type == LearningType.ACTIVE:
                return f"""Given the following initial examples:

{input_str}

Identify informative queries to improve learning.
Create a model that guides data collection.

Provide your learning results in JSON format:
{{
    "queries": ["List of informative questions"],
    "priorities": ["List of data collection priorities"],
    "metrics": {{"informativeness": 0.0-1.0}}
}}"""

            raise ValueError(f"Unsupported learning type: {context.type}")

        # Build prediction prompt using examples
        if not examples:
            raise ValueError("Examples are required for prediction")

        examples_str = json.dumps(examples, indent=2)
        return f"""Given these examples of input-output pairs:

{examples_str}

And this new input:

{input_str}

Predict the output following the same pattern.

Provide your prediction in JSON format:
{{
    "prediction": "Predicted output",
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of prediction"
}}"""

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
        try:
            # Generate prompt
            prompt = self._make_prompt(context)

            # Call language model
            response = await self._provider.complete(
                prompt=prompt,
                kwargs={
                    "model": self._config.model,
                    "temperature": self._config.temperature,
                    "max_tokens": self._config.max_tokens,
                    "stop_sequences": self._config.stop_sequences,
                },
            )

            # Get response text
            response_text = await self._get_response_text(response)

            # Parse response
            try:
                result_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LearningError(
                    f"Failed to parse language model response as JSON: {e!s}",
                    context=context,
                ) from e

            # Extract metrics
            metrics = result_json.pop("metrics", {})
            if not isinstance(metrics, dict):
                raise LearningError(
                    "Invalid metrics in language model response",
                    context=context,
                )

            # Create result
            return LearningResult(
                context_id=context.id,
                type=context.type,
                model=cast(M, result_json),
                metrics=metrics,
                metadata={"raw_response": response_text},
            )

        except Exception as e:
            if isinstance(e, LearningError):
                raise
            raise LearningError(f"Training failed: {e!s}", context=context) from e

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
        try:
            # Extract examples from model
            examples = model.get("examples", [])
            if not isinstance(examples, list):
                raise LearningError(
                    "Invalid examples in model",
                    context=context,
                )

            # Generate prompt
            prompt = self._make_prompt(context, examples)

            # Call language model
            response = await self._provider.complete(
                prompt=prompt,
                kwargs={
                    "model": self._config.model,
                    "temperature": self._config.temperature,
                    "max_tokens": self._config.max_tokens,
                    "stop_sequences": self._config.stop_sequences,
                },
            )

            # Get response text
            response_text = await self._get_response_text(response)

            # Parse response
            try:
                result_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LearningError(
                    f"Failed to parse language model response as JSON: {e!s}",
                    context=context,
                ) from e

            # Extract prediction and confidence
            prediction = result_json.get("prediction")
            if prediction is None:
                raise LearningError(
                    "Missing prediction in language model response",
                    context=context,
                )

            confidence = result_json.get("confidence", 0.0)
            if not isinstance(confidence, int | float):
                raise LearningError(
                    "Invalid confidence value in language model response",
                    context=context,
                )

            # Create result
            return PredictionResult(
                context_id=context.id,
                model_id=context.model_id,
                prediction=prediction,
                confidence=confidence,
                metadata={
                    "raw_response": response_text,
                    "reasoning": result_json.get("reasoning"),
                },
            )

        except Exception as e:
            if isinstance(e, LearningError):
                raise
            raise LearningError(f"Prediction failed: {e!s}", context=context) from e

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
        try:
            # Extract examples from evaluation data
            if not isinstance(context.data, list):
                raise LearningError(
                    "Evaluation data must be a list of examples",
                    context=context,
                )

            # Make predictions for each example
            total = len(context.data)
            correct = 0
            confidence_sum = 0.0

            for example in context.data:
                # Create prediction context
                pred_context = PredictionContext(
                    model_id=UUID(int=0),  # Dummy UUID
                    input=example.get("input"),
                )

                # Make prediction
                result = await self.predict(pred_context, model)

                # Check if prediction matches expected output
                if result.prediction == example.get("output"):
                    correct += 1
                confidence_sum += result.confidence

            # Calculate metrics
            return {
                "accuracy": correct / total if total > 0 else 0.0,
                "confidence": confidence_sum / total if total > 0 else 0.0,
            }

        except Exception as e:
            if isinstance(e, LearningError):
                raise
            raise LearningError(f"Evaluation failed: {e!s}", context=context) from e

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
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save model as JSON
            with open(path, "w") as f:
                json.dump(model, f, indent=2)

        except Exception as e:
            raise LearningError(f"Failed to save model: {e!s}") from e

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
        try:
            # Load model from JSON
            with open(path) as f:
                return cast(M, json.load(f))

        except Exception as e:
            raise LearningError(f"Failed to load model: {e!s}") from e

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
        try:
            # Train on combined data
            if isinstance(context.data, list) and "examples" in model:
                # Combine existing and new examples
                combined_data = model["examples"] + context.data
                update_context = LearningContext(
                    type=context.type,
                    data=combined_data,
                    metadata=context.metadata,
                )
                return await self.train(update_context)

            # Train on new data only
            return await self.train(context)

        except Exception as e:
            if isinstance(e, LearningError):
                raise
            raise LearningError(f"Update failed: {e!s}", context=context) from e

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
        try:
            # Create empty model with same structure
            empty_model: dict[str, Any] = {
                key: (
                    []
                    if isinstance(value, list)
                    else {}
                    if isinstance(value, dict)
                    else None
                )
                for key, value in model.items()
            }
            return cast(M, empty_model)

        except Exception as e:
            raise LearningError(f"Failed to reset model: {e!s}") from e

    def update_context(self, context: LearningContext[T]) -> LearningContext[T]:
        """Update context with new data.

        Args:
            context: Learning context to update

        Returns:
            Updated learning context
        """
        return context  # Default implementation just returns the context unchanged
