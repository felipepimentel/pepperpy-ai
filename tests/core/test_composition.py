"""Tests for the composition module."""

import json
import os
import tempfile

import pytest

from pepperpy.core.composition import (
    Outputs,
    Pipeline,
    Processors,
    Sources,
    compose,
)
from pepperpy.core.pipeline.base import PipelineContext


@pytest.mark.asyncio
async def test_text_source():
    """Test text source factory."""
    source = Sources.text("hello")
    assert source() == "hello"


@pytest.mark.asyncio
async def test_file_source():
    """Test file source factory."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("hello")
        path = f.name

    try:
        source = Sources.file(path)
        assert source() == "hello"
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_json_source():
    """Test JSON source factory."""
    data = {"key": "value"}
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(data, f)
        path = f.name

    try:
        source = Sources.json(path)
        assert source() == data
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_transform_processor():
    """Test transform processor factory."""
    processor = Processors.transform(str.upper)
    context = PipelineContext()
    result = processor("hello", context)
    assert result == "HELLO"
    assert context.get_metadata("transform_result") == "HELLO"


@pytest.mark.asyncio
async def test_filter_processor():
    """Test filter processor factory."""
    processor = Processors.filter(lambda x: len(x) > 3)
    context = PipelineContext()

    # Test passing value
    result = processor("hello", context)
    assert result == "hello"
    assert context.get_metadata("filter_result") is True

    # Test filtered value
    result = processor("hi", context)
    assert result is None
    assert context.get_metadata("filter_result") is False


@pytest.mark.asyncio
async def test_map_processor():
    """Test map processor factory."""
    processor = Processors.map(str.upper)
    context = PipelineContext()
    result = processor(["hello", "world"], context)
    assert result == ["HELLO", "WORLD"]
    assert context.get_metadata("map_result") == ["HELLO", "WORLD"]


@pytest.mark.asyncio
async def test_console_output(capsys):
    """Test console output factory."""
    output = Outputs.console()
    context = PipelineContext()
    result = output("hello", context)
    assert result == "hello"
    assert context.get_metadata("console_output") == "hello"
    captured = capsys.readouterr()
    assert captured.out.strip() == "hello"


@pytest.mark.asyncio
async def test_file_output():
    """Test file output factory."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        path = f.name

    try:
        output = Outputs.file(path)
        context = PipelineContext()
        result = output("hello", context)
        assert result == "hello"
        assert context.get_metadata("file_output") == path
        with open(path, "r") as f:
            assert f.read() == "hello"
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_json_output():
    """Test JSON output factory."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        path = f.name

    try:
        data = {"key": "value"}
        output = Outputs.json(path)
        context = PipelineContext()
        result = output(data, context)
        assert result == data
        assert context.get_metadata("json_output") == path
        with open(path, "r") as f:
            assert json.load(f) == data
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_pipeline_composition():
    """Test pipeline composition."""
    # Create pipeline
    pipeline = compose("test")
    pipeline.source(Sources.text("hello"))
    pipeline.process(Processors.transform(str.upper))
    pipeline.output(Outputs.console())

    # Execute pipeline
    context = PipelineContext()
    result = await pipeline.execute(context)

    # Check results
    assert result == "HELLO"
    assert context.get_metadata("source_data") == "hello"
    assert context.get_metadata("transform_result") == "HELLO"
    assert context.get_metadata("console_output") == "HELLO"
    assert context.get_metadata("final_result") == "HELLO"


@pytest.mark.asyncio
async def test_pipeline_type_safety():
    """Test pipeline type safety."""
    # Create pipeline with explicit types
    pipeline = Pipeline[str, str]("test")
    pipeline.source(Sources.text("hello"))
    pipeline.process(Processors.transform(str.upper))
    pipeline.output(Outputs.console())

    # Execute pipeline
    context = PipelineContext()
    result = await pipeline.execute(context)
    assert result == "HELLO"


@pytest.mark.asyncio
async def test_pipeline_without_source():
    """Test pipeline execution without source."""
    pipeline = compose("test")
    with pytest.raises(ValueError) as exc:
        await pipeline.execute()
    assert str(exc.value) == "No source configured for pipeline"


@pytest.mark.asyncio
async def test_pipeline_context_creation():
    """Test automatic context creation."""
    pipeline = compose("test")
    pipeline.source(Sources.text("hello"))
    result = await pipeline.execute()  # No context provided
    assert result == "hello"
