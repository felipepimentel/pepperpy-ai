"""@file: test_processors.py
@purpose: Test content processing system
@component: Tests > Core > Processors
@created: 2024-03-21
@task: TASK-007-R060
@status: active
"""

import pytest
from typing import Dict, Any

from pepperpy.core.processors import (
    ContentProcessor,
    ProcessingContext,
    ProcessingResult,
    ProcessorRegistry,
    TextProcessor,
    CodeProcessor,
)

@pytest.fixture
def text_processor():
    """Create a text processor for testing."""
    return TextProcessor(config={"max_length": 100})

@pytest.fixture
def code_processor():
    """Create a code processor for testing."""
    return CodeProcessor(language="python")

@pytest.fixture
def registry():
    """Get processor registry instance."""
    return ProcessorRegistry.get_instance()

async def test_text_processor_basic(text_processor: TextProcessor):
    """Test basic text processing."""
    content = "  Hello World  "
    context = ProcessingContext(
        content_type="text",
        metadata={},
        options={"normalize": True}
    )
    
    result = await text_processor.process(content, context)
    
    assert result.content == "Hello World"
    assert not result.errors
    assert not result.warnings
    assert result.processing_time > 0

async def test_text_processor_options(text_processor: TextProcessor):
    """Test text processor options."""
    content = "Hello World"
    context = ProcessingContext(
        content_type="text",
        metadata={},
        options={
            "lowercase": True,
            "max_length": 5
        }
    )
    
    result = await text_processor.process(content, context)
    
    assert result.content == "hello"
    assert not result.errors
    assert not result.warnings

async def test_code_processor_basic(code_processor: CodeProcessor):
    """Test basic code processing."""
    content = "def hello(): pass"
    context = ProcessingContext(
        content_type="code",
        metadata={},
        options={"format": True}
    )
    
    result = await code_processor.process(content, context)
    
    assert result.content == content
    assert not result.errors
    assert not result.warnings
    assert result.processing_time > 0

async def test_processor_registry(
    registry: ProcessorRegistry,
    text_processor: TextProcessor,
    code_processor: CodeProcessor
):
    """Test processor registry."""
    # Register processors
    registry.register("text", "1.0", text_processor)
    registry.register("code", "1.0", code_processor)
    
    # Get processors
    text_proc = await registry.get_processor("text")
    code_proc = await registry.get_processor("code")
    
    assert isinstance(text_proc, TextProcessor)
    assert isinstance(code_proc, CodeProcessor)
    
    # List processors
    processors = registry.list_processors()
    assert "text" in processors
    assert "code" in processors
    assert "1.0" in processors["text"]
    assert "1.0" in processors["code"]

async def test_processor_validation(text_processor: TextProcessor):
    """Test content validation."""
    # Test empty content
    content = ""
    context = ProcessingContext(
        content_type="text",
        metadata={},
        options={}
    )
    
    errors = await text_processor.validate(content, context)
    assert "Empty content" in errors
    
    # Test content too long
    content = "x" * 1000001
    errors = await text_processor.validate(content, context)
    assert "Content too long" in errors

async def test_processor_error_handling(text_processor: TextProcessor):
    """Test error handling."""
    # Simulate error by passing None
    content = None
    context = ProcessingContext(
        content_type="text",
        metadata={},
        options={}
    )
    
    result = await text_processor.process(content, context)  # type: ignore
    
    assert result.errors
    assert "error" in result.metadata
    assert result.processing_time > 0 