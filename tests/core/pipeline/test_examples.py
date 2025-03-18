"""Tests for the pepperpy.core.pipeline.examples module.

This module contains integration tests for the example pipelines
defined in pepperpy.core.pipeline.examples.
"""

import pytest

from pepperpy.core.pipeline.base import PipelineContext
from pepperpy.core.pipeline.examples import (
    create_branching_pipeline,
    create_conditional_pipeline,
    create_data_processing_pipeline,
)


class TestDataProcessingPipeline:
    """Tests for the data processing pipeline example."""

    def test_data_processing_pipeline(self):
        """Test the data processing pipeline example."""
        pipeline = create_data_processing_pipeline()

        # Configure context with required fields and transforms
        context = PipelineContext()
        context.set("required_fields", ["name", "age", "email"])
        context.set(
            "transforms",
            {
                "name": str.strip,
                "age": lambda x: int(x) if x is not None else None,
            },
        )

        # Create test input
        input_data = {
            "name": "  John Doe  ",
            "email": "john@example.com",
        }

        # Execute pipeline
        result = pipeline.execute(input_data, context)

        # Verify transformations
        assert result["name"] == "John Doe"  # Whitespace stripped
        assert result["email"] == "john@example.com"  # Unchanged
        assert result["age"] is None  # Missing field filled with None

        # Verify metadata
        assert context.get_metadata("validated") is True
        missing_fields = context.get_metadata("missing_fields")
        assert "age" in missing_fields

    def test_data_processing_with_scalar_input(self):
        """Test the data processing pipeline with scalar input."""
        pipeline = create_data_processing_pipeline()
        context = PipelineContext()

        # Execute with a scalar value
        result = pipeline.execute("test_value", context)

        # Should convert to dict
        assert isinstance(result, dict)
        assert result["value"] == "test_value"

    def test_data_processing_with_transforms(self):
        """Test the data processing pipeline with complex transforms."""
        pipeline = create_data_processing_pipeline()

        # Create context with transforms
        context = PipelineContext()
        context.set("required_fields", ["name", "age", "score"])

        # Define some transforms
        class UppercaseTransform:
            def transform(self, value):
                return value.upper() if isinstance(value, str) else value

        context.set(
            "transforms",
            {
                "name": UppercaseTransform(),
                "age": lambda x: int(x) if x is not None else 0,
                "score": lambda x: float(x) * 1.1 if x is not None else 0.0,
            },
        )

        # Create test input
        input_data = {
            "name": "jane smith",
            "age": "25",
            "score": 90,
        }

        # Execute pipeline
        result = pipeline.execute(input_data, context)

        # Verify transformations
        assert result["name"] == "JANE SMITH"  # Uppercase
        assert result["age"] == 25  # Converted to int
        assert result["score"] == 99.0  # Increased by 10%


class TestConditionalPipeline:
    """Tests for the conditional pipeline example."""

    def test_conditional_pipeline_with_list(self):
        """Test the conditional pipeline with a list input."""
        pipeline = create_conditional_pipeline()

        # Test with list input
        list_data = [1, 2, 3, 4, 5]
        context = PipelineContext()

        result = pipeline.execute(list_data, context)

        # Verify result format
        assert result["type"] == "list"
        assert result["count"] == 5
        assert result["items"] == list_data

        # Verify metadata
        assert context.get_metadata("is_list") is True

    def test_conditional_pipeline_with_scalar(self):
        """Test the conditional pipeline with a scalar input."""
        pipeline = create_conditional_pipeline()

        # Test with scalar input
        scalar_data = "test string"
        context = PipelineContext()

        result = pipeline.execute(scalar_data, context)

        # Verify result format
        assert result["type"] == "single"
        assert result["value"] == scalar_data

        # Verify metadata
        assert context.get_metadata("is_list") is False


class TestBranchingPipeline:
    """Tests for the branching pipeline example."""

    def test_branching_pipeline_with_numeric_data(self):
        """Test the branching pipeline with numeric data."""
        pipeline = create_branching_pipeline()

        # Test with numeric data
        numeric_data = [10, 20, 30, 40, 50]
        context = PipelineContext()
        context.set_metadata("data_type", "numeric")

        result = pipeline.execute(numeric_data, context)

        # Verify structure
        assert "results" in result
        results = result["results"]

        # Verify branch results
        assert results["count"] == 5
        assert "List with 5 items" in results["summary"]

        # Verify stats for numeric data
        assert results["stats"]["type"] == "list"
        assert results["stats"]["min"] == 10
        assert results["stats"]["max"] == 50
        assert results["stats"]["avg"] == 30.0

        # Verify metadata preservation
        assert result["metadata"]["data_type"] == "numeric"

    def test_branching_pipeline_with_string_data(self):
        """Test the branching pipeline with string data."""
        pipeline = create_branching_pipeline()

        # Test with string data
        string_data = "PepperPy Pipeline"
        context = PipelineContext()
        context.set_metadata("data_type", "string")

        result = pipeline.execute(string_data, context)

        # Verify structure
        assert "results" in result
        results = result["results"]

        # Verify branch results
        assert results["count"] == 17  # Length of "PepperPy Pipeline"
        assert "String of length 17" in results["summary"]

        # Verify stats for string data
        assert results["stats"]["type"] == "str"

        # No numeric stats for string data
        assert "min" not in results["stats"]
        assert "max" not in results["stats"]
        assert "avg" not in results["stats"]

        # Verify metadata preservation
        assert result["metadata"]["data_type"] == "string"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
