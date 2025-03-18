#!/usr/bin/env python3
"""Example of migrating a transform pipeline to the unified pipeline framework.

This example demonstrates the process of migrating an existing transform pipeline
implementation to use the new unified pipeline framework through the adapter
pattern.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from pepperpy.core.pipeline.base import PipelineContext
from pepperpy.data.transform import Transform, TransformType
from pepperpy.data.transform.adapter import TransformPipelineBuilderAdapter
from pepperpy.data.validation import (
    ValidationHook,
    ValidationLevel,
    ValidationResult,
    ValidationStage,
    Validator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Example transforms
class UppercaseTransform(Transform):
    """Transform that converts text to uppercase."""

    def __init__(self, name: str = "uppercase"):
        """Initialize the transform."""
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of the transform."""
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the transform type."""
        return TransformType.CLASS

    def transform(self, data: Any) -> Any:
        """Transform the data to uppercase."""
        if isinstance(data, str):
            return data.upper()
        if isinstance(data, list):
            return [self.transform(item) for item in data]
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary."""
        return {
            "name": self.name,
            "type": self.transform_type.value,
        }


class ReverseTransform(Transform):
    """Transform that reverses text."""

    def __init__(self, name: str = "reverse"):
        """Initialize the transform."""
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of the transform."""
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the transform type."""
        return TransformType.CLASS

    def transform(self, data: Any) -> Any:
        """Transform the data by reversing it."""
        if isinstance(data, str):
            return data[::-1]
        if isinstance(data, list):
            return [self.transform(item) for item in data]
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary."""
        return {
            "name": self.name,
            "type": self.transform_type.value,
        }


# Example validator
class LengthValidator(Validator):
    """Validator that checks text length."""

    def __init__(
        self, name: str = "length_validator", min_length: int = 1, max_length: int = 100
    ):
        """Initialize the validator.

        Args:
            name: The name of the validator
            min_length: The minimum allowed length
            max_length: The maximum allowed length
        """
        self._name = name
        self._min_length = min_length
        self._max_length = max_length

    @property
    def name(self) -> str:
        """Get the name of the validator."""
        return self._name

    def validate(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate the data length.

        Args:
            data: The data to validate
            context: The validation context

        Returns:
            The validation result
        """
        if not isinstance(data, str):
            return ValidationResult(
                is_valid=False,
                errors={"type": "Data must be a string"},
            )

        length = len(data)
        if length < self._min_length:
            return ValidationResult(
                is_valid=False,
                errors={
                    "length": f"Length {length} is less than minimum {self._min_length}"
                },
            )

        if length > self._max_length:
            return ValidationResult(
                is_valid=False,
                errors={
                    "length": f"Length {length} exceeds maximum {self._max_length}"
                },
            )

        return ValidationResult(is_valid=True)


async def run_example():
    """Run the example."""
    logger.info("Starting transform pipeline migration example")

    # Create transforms
    uppercase = UppercaseTransform()
    reverse = ReverseTransform()

    # Create validator
    validator = LengthValidator(min_length=3, max_length=50)

    # Create validation hooks
    pre_hook = ValidationHook(validator, ValidationStage.PRE_TRANSFORM)
    post_hook = ValidationHook(validator, ValidationStage.POST_TRANSFORM)
    intermediate_hook = ValidationHook(validator, ValidationStage.INTERMEDIATE)

    # Build the pipeline using the adapter
    logger.info("Building transform pipeline using the adapter")
    pipeline = (
        TransformPipelineBuilderAdapter()
        .with_name("example_transform_pipeline")
        .with_transform(
            name="uppercase",
            transform=uppercase,
            pre_hooks=[pre_hook],
            post_hooks=[post_hook],
        )
        .with_transform(
            name="reverse",
            transform=reverse,
            pre_hooks=[pre_hook],
            post_hooks=[post_hook],
        )
        .with_intermediate_validation([intermediate_hook])
        .with_validation_levels([ValidationLevel.STANDARD])
        .build()
    )

    # Create a context with metadata
    context = PipelineContext()
    context.set_metadata("user_id", "user_123")
    context.set_metadata("session_id", "session_456")

    # Test cases
    test_cases = [
        "Hello, World!",  # Valid input
        "Hi",  # Too short
        "This is a very long string that exceeds the maximum length limit of fifty characters",  # Too long
        ["Hello", "World"],  # List input
    ]

    # Execute the pipeline for each test case
    for data in test_cases:
        try:
            logger.info(f"Processing: {data}")
            result = await pipeline.execute_async(data, context)
            logger.info(f"Result: {result}")
            logger.info(f"Last stage: {context.get('last_stage')}")
            logger.info(f"Last result: {context.get('last_result')}")
            logger.info(f"Validation errors: {context.get('validation_errors')}")
            logger.info("-" * 50)
        except Exception as e:
            logger.error(f"Error processing {data}: {e}")
            logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_example())
