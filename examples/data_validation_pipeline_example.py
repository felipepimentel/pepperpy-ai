#!/usr/bin/env python
"""Example demonstrating the data transformation pipeline with validation hooks.

This example shows how to create and use a data transformation pipeline with
validation hooks to validate data at various stages of transformation.
"""

import json
from typing import Any, Dict

from pepperpy.data.transform import (
    register_function_transform,
)
from pepperpy.data.transform_pipeline import (
    ValidationLevel,
    create_validated_pipeline,
    execute_validated_pipeline,
)
from pepperpy.data.validation import (
    ValidationResult,
    register_function_validator,
)


# Define some simple data transformations
def uppercase_transform(data: str) -> str:
    """Transform text to uppercase."""
    return data.upper()


def add_greeting_transform(data: str) -> str:
    """Add a greeting to text."""
    return f"Hello, {data}!"


def remove_punctuation_transform(data: str) -> str:
    """Remove punctuation from text."""
    return "".join(c for c in data if c.isalnum() or c.isspace())


# Define some simple validators
def length_validator(data: Any) -> ValidationResult:
    """Validate that data is not too long."""
    if isinstance(data, str) and len(data) > 50:
        return ValidationResult(
            False, errors={"length": f"Text is too long ({len(data)} > 50)"}
        )
    return ValidationResult(True, data=data)


def content_validator(data: Any) -> ValidationResult:
    """Validate that data contains only allowed characters."""
    if isinstance(data, str):
        disallowed = [
            c for c in data if not (c.isalnum() or c.isspace() or c in ",.!?")
        ]
        if disallowed:
            return ValidationResult(
                False,
                errors={
                    "content": f"Text contains disallowed characters: {', '.join(disallowed)}"
                },
            )
    return ValidationResult(True, data=data)


def uppercase_validator(data: Any) -> ValidationResult:
    """Validate that data is uppercase."""
    if isinstance(data, str) and not data.isupper():
        return ValidationResult(False, errors={"case": "Text must be uppercase"})
    return ValidationResult(True, data=data)


def main() -> None:
    """Run the example."""
    # Register transforms
    register_function_transform("uppercase", uppercase_transform)
    register_function_transform("add_greeting", add_greeting_transform)
    register_function_transform("remove_punctuation", remove_punctuation_transform)

    # Register validators
    register_function_validator("length", length_validator)
    register_function_validator("content", content_validator)
    register_function_validator("uppercase", uppercase_validator)

    # Create a validated pipeline
    pipeline = create_validated_pipeline(
        name="text_processing_pipeline",
        transforms=["remove_punctuation", "uppercase", "add_greeting"],
        validators=["length", "content", "uppercase"],
        pre_validation=True,
        post_validation=True,
        intermediate_validation=True,
        validation_levels=[ValidationLevel.BASIC, ValidationLevel.STANDARD],
        fail_fast=False,
    )

    # Print pipeline information
    print("Pipeline Information:")
    print(f"  Name: {pipeline.name}")
    print(f"  Stages: {len(pipeline.stages)}")
    print(
        f"  Validation Levels: {[level.value for level in pipeline.validation_levels]}"
    )
    print(f"  Intermediate Hooks: {len(pipeline.intermediate_hooks)}")
    print()

    # Process some valid data
    try:
        print("Processing valid data:")
        input_data = "John Doe"
        print(f"  Input: {input_data!r}")

        # Create a context to capture validation results
        context: Dict[str, Any] = {}

        # Execute the pipeline
        result = execute_validated_pipeline(
            "text_processing_pipeline", input_data, context
        )
        print(f"  Result: {result!r}")

        # Print validation errors (should be empty)
        if "validation_errors" in context:
            print("  Validation Errors:")
            for stage, errors in context["validation_errors"].items():
                if errors:
                    print(f"    {stage}: {json.dumps(errors, indent=2)}")
                else:
                    print(f"    {stage}: No errors")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

    # Process some invalid data (should fail uppercase validation after the first transform)
    try:
        print("Processing invalid data (mixed case):")
        input_data = "John Doe 123"
        print(f"  Input: {input_data!r}")

        # Create a context to capture validation results
        context = {}

        # Execute the pipeline
        result = execute_validated_pipeline(
            "text_processing_pipeline", input_data, context
        )
        print(f"  Result: {result!r}")

        # Print validation errors
        if "validation_errors" in context:
            print("  Validation Errors:")
            for stage, errors in context["validation_errors"].items():
                if errors:
                    print(f"    {stage}: {json.dumps(errors, indent=2)}")
                else:
                    print(f"    {stage}: No errors")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

    # Process some invalid data (with disallowed characters)
    try:
        print("Processing invalid data (disallowed characters):")
        input_data = "John Doe @#$%"
        print(f"  Input: {input_data!r}")

        # Create a context to capture validation results
        context = {}

        # Execute the pipeline
        result = execute_validated_pipeline(
            "text_processing_pipeline", input_data, context
        )
        print(f"  Result: {result!r}")

        # Print validation errors
        if "validation_errors" in context:
            print("  Validation Errors:")
            for stage, errors in context["validation_errors"].items():
                if errors:
                    print(f"    {stage}: {json.dumps(errors, indent=2)}")
                else:
                    print(f"    {stage}: No errors")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

    # Process some invalid data with fail_fast=True
    try:
        print("Processing invalid data with fail_fast=True:")
        input_data = "John Doe @#$%"
        print(f"  Input: {input_data!r}")

        # Create a new pipeline with fail_fast=True
        pipeline = create_validated_pipeline(
            name="text_processing_pipeline_fail_fast",
            transforms=["remove_punctuation", "uppercase", "add_greeting"],
            validators=["length", "content", "uppercase"],
            pre_validation=True,
            post_validation=True,
            intermediate_validation=True,
            validation_levels=[ValidationLevel.BASIC, ValidationLevel.STANDARD],
            fail_fast=True,
        )

        # Execute the pipeline
        result = execute_validated_pipeline(
            "text_processing_pipeline_fail_fast", input_data
        )
        print(f"  Result: {result!r}")
    except Exception as e:
        print(f"  Error: {e}")
        print()

    # Process data with different validation levels
    try:
        print("Processing data with STRICT validation level:")
        input_data = "John Doe"
        print(f"  Input: {input_data!r}")

        # Create a new pipeline with STRICT validation level
        pipeline = create_validated_pipeline(
            name="text_processing_pipeline_strict",
            transforms=["remove_punctuation", "uppercase", "add_greeting"],
            validators=["length", "content", "uppercase"],
            pre_validation=True,
            post_validation=True,
            intermediate_validation=True,
            validation_levels=[ValidationLevel.STRICT],
            fail_fast=True,
        )

        # Create a context to capture validation results
        context = {}

        # Execute the pipeline
        result = execute_validated_pipeline(
            "text_processing_pipeline_strict", input_data, context
        )
        print(f"  Result: {result!r}")

        # Print validation errors
        if "validation_errors" in context:
            print("  Validation Errors:")
            for stage, errors in context["validation_errors"].items():
                if errors:
                    print(f"    {stage}: {json.dumps(errors, indent=2)}")
                else:
                    print(f"    {stage}: No errors")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()


if __name__ == "__main__":
    main()
