"""Tests for the pepperpy.core.pipeline.stages module.

This module contains tests for the common pipeline stages defined in
pepperpy.core.pipeline.stages, including:
- FunctionStage
- TransformStage
- ConditionalStage
- BranchingStage
"""

from typing import Any, TypeVar
from unittest.mock import Mock

import pytest

from pepperpy.core.pipeline.base import PipelineContext, PipelineError
from pepperpy.core.pipeline.stages import (
    BranchingStage,
    ConditionalStage,
    FunctionStage,
    TransformStage,
)

# Type variables for testing
T = TypeVar("T")
U = TypeVar("U")


class TestFunctionStage:
    """Tests for the FunctionStage class."""

    def test_function_stage_execution(self):
        """Test basic function stage execution."""
        # Create a mock function
        mock_func = Mock(return_value="processed")
        stage = FunctionStage(name="test_function", func=mock_func)

        # Create context and execute stage
        context = PipelineContext()
        result = stage(input_data="test_input", context=context)

        # Verify results
        assert result == "processed"
        mock_func.assert_called_once_with("test_input", context)

    def test_function_stage_with_exception(self):
        """Test function stage handling exceptions."""

        # Create a function that raises an exception
        def failing_func(data: Any, ctx: PipelineContext) -> Any:
            raise ValueError("Test exception")

        stage = FunctionStage(name="failing_function", func=failing_func)
        context = PipelineContext()

        # Verify exception handling
        with pytest.raises(PipelineError) as excinfo:
            stage("test_input", context)

        assert "Test exception" in str(excinfo.value)
        assert "failing_function" in str(excinfo.value)

    def test_function_stage_with_context_manipulation(self):
        """Test function stage that manipulates context."""

        # Create a function that updates context
        def context_updater(data: str, ctx: PipelineContext) -> str:
            ctx.set("processed", True)
            ctx.set_metadata("timestamp", "2023-01-01")
            return data.upper()

        stage = FunctionStage(name="context_updater", func=context_updater)
        context = PipelineContext()

        # Execute stage
        result = stage("test", context)

        # Verify context updates
        assert result == "TEST"
        assert context.get("processed") is True
        assert context.get_metadata("timestamp") == "2023-01-01"


class TestTransformStage:
    """Tests for the TransformStage class."""

    def test_transform_stage_with_callable(self):
        """Test transform stage with a callable transform."""
        # Create a simple transform function
        transform = lambda x: x.upper()
        stage = TransformStage(name="callable_transform", transform=transform)

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify result
        assert result == "TEST"

    def test_transform_stage_with_object(self):
        """Test transform stage with an object having transform method."""

        # Create a transform object
        class Transformer:
            def transform(self, data):
                return f"Transformed: {data}"

        transform = Transformer()
        stage = TransformStage(name="object_transform", transform=transform)

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify result
        assert result == "Transformed: test"

    def test_transform_stage_with_name_lookup(self):
        """Test transform stage with transform name lookup in context."""

        # Create a transform object
        class Transformer:
            def transform(self, data):
                return f"Lookup Transform: {data}"

        # Create context with transform
        context = PipelineContext()
        context.set("transforms", {"my_transform": Transformer()})

        # Create stage with transform name
        stage = TransformStage(name="lookup_transform", transform="my_transform")

        # Execute stage
        result = stage("test", context)

        # Verify result
        assert result == "Lookup Transform: test"

    def test_transform_stage_with_missing_transform(self):
        """Test transform stage with missing transform in context."""
        stage = TransformStage(name="missing_transform", transform="non_existent")
        context = PipelineContext()

        # Verify exception
        with pytest.raises(PipelineError) as excinfo:
            stage("test", context)

        assert "not found in context" in str(excinfo.value)

    def test_transform_stage_with_invalid_transform(self):
        """Test transform stage with invalid transform object."""
        # Use an integer as an invalid transform
        stage = TransformStage(name="invalid_transform", transform=42)
        context = PipelineContext()

        # Verify exception
        with pytest.raises(PipelineError) as excinfo:
            stage("test", context)

        assert "Invalid transform" in str(excinfo.value)


class TestConditionalStage:
    """Tests for the ConditionalStage class."""

    def test_conditional_stage_true_condition(self):
        """Test conditional stage with true condition."""
        # Create stages and condition
        true_stage = FunctionStage(name="true_stage", func=lambda x, _: f"TRUE: {x}")
        false_stage = FunctionStage(name="false_stage", func=lambda x, _: f"FALSE: {x}")
        condition = lambda x, _: True

        # Create conditional stage
        stage = ConditionalStage(
            name="conditional",
            condition=condition,
            if_true=true_stage,
            if_false=false_stage,
        )

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify result
        assert result == "TRUE: test"

    def test_conditional_stage_false_condition(self):
        """Test conditional stage with false condition."""
        # Create stages and condition
        true_stage = FunctionStage(name="true_stage", func=lambda x, _: f"TRUE: {x}")
        false_stage = FunctionStage(name="false_stage", func=lambda x, _: f"FALSE: {x}")
        condition = lambda x, _: False

        # Create conditional stage
        stage = ConditionalStage(
            name="conditional",
            condition=condition,
            if_true=true_stage,
            if_false=false_stage,
        )

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify result
        assert result == "FALSE: test"

    def test_conditional_stage_false_without_else(self):
        """Test conditional stage with false condition and no else branch."""
        # Create stage and condition
        true_stage = FunctionStage(name="true_stage", func=lambda x, _: f"TRUE: {x}")
        condition = lambda x, _: False

        # Create conditional stage with no if_false
        stage = ConditionalStage(
            name="conditional", condition=condition, if_true=true_stage, if_false=None
        )

        # Execute stage - should return input unchanged
        context = PipelineContext()
        result = stage("test", context)

        # Verify result is the original input
        assert result == "test"

    def test_conditional_stage_with_exception(self):
        """Test conditional stage handling exceptions in condition."""

        # Create a condition that raises an exception
        def failing_condition(data: Any, ctx: PipelineContext) -> bool:
            raise ValueError("Condition error")

        true_stage = FunctionStage(name="true_stage", func=lambda x, _: f"TRUE: {x}")

        # Create conditional stage
        stage = ConditionalStage(
            name="failing_conditional", condition=failing_condition, if_true=true_stage
        )

        # Verify exception handling
        context = PipelineContext()
        with pytest.raises(PipelineError) as excinfo:
            stage("test", context)

        assert "Condition error" in str(excinfo.value)
        assert "failing_conditional" in str(excinfo.value)


class TestBranchingStage:
    """Tests for the BranchingStage class."""

    def test_branching_stage_execution(self):
        """Test basic branching stage execution."""
        # Create branch stages
        upper_stage = FunctionStage(name="upper", func=lambda x, _: x.upper())
        length_stage = FunctionStage(name="length", func=lambda x, _: len(cast(str, x)))
        reverse_stage = FunctionStage(name="reverse", func=lambda x, _: x[::-1])

        # Create branching stage
        stage = BranchingStage(
            name="branching",
            branches={
                "upper": upper_stage,
                "length": length_stage,
                "reverse": reverse_stage,
            },
        )

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify results
        assert isinstance(result, dict)
        assert result["upper"] == "TEST"
        assert result["length"] == 4
        assert result["reverse"] == "tset"

    def test_branching_stage_with_empty_branches(self):
        """Test branching stage with no branches."""
        # Create empty branching stage
        stage = BranchingStage(name="empty_branching", branches={})

        # Execute stage
        context = PipelineContext()
        result = stage("test", context)

        # Verify results
        assert isinstance(result, dict)
        assert result == {}

    def test_branching_stage_with_context_isolation(self):
        """Test that branch contexts are isolated."""

        # Create stages that modify context
        def modify_context_a(data: str, ctx: PipelineContext) -> str:
            ctx.set("branch_data", "A")
            return "A"

        def modify_context_b(data: str, ctx: PipelineContext) -> str:
            ctx.set("branch_data", "B")
            return "B"

        stage_a = FunctionStage(name="branch_a", func=modify_context_a)
        stage_b = FunctionStage(name="branch_b", func=modify_context_b)

        # Create branching stage
        stage = BranchingStage(
            name="context_branching",
            branches={
                "a": stage_a,
                "b": stage_b,
            },
        )

        # Execute stage
        main_context = PipelineContext()
        result = stage("test", main_context)

        # Verify results
        assert result["a"] == "A"
        assert result["b"] == "B"

        # The main context should be unmodified
        assert main_context.get("branch_data") is None

    def test_branching_stage_with_exception(self):
        """Test branching stage with an exception in one branch."""
        # Create stages, one that fails
        normal_stage = FunctionStage(name="normal", func=lambda x, _: x.upper())

        def failing_func(data: Any, ctx: PipelineContext) -> Any:
            raise ValueError("Branch failure")

        failing_stage = FunctionStage(name="failing", func=failing_func)

        # Create branching stage
        stage = BranchingStage(
            name="exception_branching",
            branches={
                "normal": normal_stage,
                "failing": failing_stage,
            },
        )

        # Verify exception handling
        context = PipelineContext()
        with pytest.raises(PipelineError) as excinfo:
            stage("test", context)

        assert "Branch failure" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
