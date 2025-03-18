"""Tests for the pipeline module."""

import pytest

from pepperpy.core.pipeline import (
    FunctionStage,
    Pipeline,
    PipelineContext,
    PipelineRegistry,
    PipelineStage,
)


@pytest.mark.asyncio
async def test_pipeline_context():
    """Test pipeline context."""
    context = PipelineContext()

    # Test metadata
    context.set_metadata("key", "value")
    assert context.get_metadata("key") == "value"
    assert context.get_metadata("missing") is None
    assert context.get_metadata("missing", "default") == "default"


@pytest.mark.asyncio
async def test_pipeline_stage():
    """Test pipeline stage."""
    # Test base stage
    stage = PipelineStage("test", "Test stage")
    assert stage.name == "test"
    assert stage.description == "Test stage"

    # Test execute not implemented
    with pytest.raises(NotImplementedError):
        await stage.execute("data", PipelineContext())


@pytest.mark.asyncio
async def test_function_stage():
    """Test function stage."""

    # Test synchronous function
    def upper(data: str, context: PipelineContext) -> str:
        context.set_metadata("called", True)
        return data.upper()

    stage = FunctionStage("test", upper)
    context = PipelineContext()
    result = await stage.execute("hello", context)
    assert result == "HELLO"
    assert context.get_metadata("called") is True


@pytest.mark.asyncio
async def test_pipeline():
    """Test pipeline."""
    # Create pipeline
    pipeline = Pipeline("test")
    assert pipeline.name == "test"
    assert len(pipeline.stages) == 0

    # Add stages
    stage1 = FunctionStage("stage1", lambda x, ctx: x.upper())
    stage2 = FunctionStage("stage2", lambda x, ctx: f"_{x}_")
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    assert len(pipeline.stages) == 2

    # Execute pipeline
    context = PipelineContext()
    result = await pipeline.execute("hello", context)
    assert result == "_HELLO_"


def test_pipeline_registry():
    """Test pipeline registry."""
    registry = PipelineRegistry()
    assert len(registry.list()) == 0

    # Register pipeline
    pipeline = Pipeline("test")
    registry.register(pipeline)
    assert len(registry.list()) == 1
    assert registry.get("test") == pipeline

    # Test duplicate registration
    with pytest.raises(ValueError):
        registry.register(pipeline)

    # Test unregister
    registry.unregister("test")
    assert len(registry.list()) == 0
    assert registry.get("test") is None

    # Test clear
    registry.register(pipeline)
    registry.clear()
    assert len(registry.list()) == 0
