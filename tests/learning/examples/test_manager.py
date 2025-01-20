"""Tests for example manager functionality."""

import pytest
from datetime import datetime
from typing import Set

from pepperpy.learning.examples import Example, ExampleManager

@pytest.mark.asyncio
async def test_add_example_from_interaction(example_manager: ExampleManager):
    """Test adding an example from interaction."""
    example = await example_manager.add_example_from_interaction(
        input_text="test input",
        output_text="test output",
        tags={"tag1", "tag2"},
        metadata={"source": "test"}
    )
    
    assert example.input_text == "test input"
    assert example.output_text == "test output"
    assert example.tags == {"tag1", "tag2"}
    assert example.metadata["source"] == "test"
    assert "added_at" in example.metadata
    assert example.metadata["source"] == "test"
    assert isinstance(example.created_at, datetime)
    assert isinstance(example.updated_at, datetime)
    
    # Verify example was stored
    stored = example_manager.store.get_example(example.example_id)
    assert stored is not None
    assert stored.input_text == example.input_text
    assert stored.tags == example.tags

@pytest.mark.asyncio
async def test_select_examples(example_manager: ExampleManager):
    """Test selecting relevant examples."""
    # Add test examples
    await example_manager.add_example_from_interaction(
        input_text="test math addition",
        output_text="2 + 2 = 4",
        tags={"math", "addition"}
    )
    await example_manager.add_example_from_interaction(
        input_text="test math multiplication",
        output_text="3 * 4 = 12",
        tags={"math", "multiplication"}
    )
    await example_manager.add_example_from_interaction(
        input_text="test grammar",
        output_text="correct sentence",
        tags={"grammar"}
    )
    
    # Test selection with required tags
    examples = await example_manager.select_examples(
        task_description="solve math problem",
        required_tags={"math"}
    )
    assert len(examples) == 2
    assert all("math" in ex.tags for ex in examples)
    
    # Test selection with excluded tags
    examples = await example_manager.select_examples(
        task_description="solve math problem",
        required_tags={"math"},
        exclude_tags={"multiplication"}
    )
    assert len(examples) == 1
    assert "addition" in examples[0].tags
    
    # Test selection with limit
    examples = await example_manager.select_examples(
        task_description="solve math problem",
        required_tags={"math"},
        num_examples=1
    )
    assert len(examples) == 1

@pytest.mark.asyncio
async def test_format_examples(example_manager: ExampleManager):
    """Test formatting examples for prompts."""
    # Add test examples
    example1 = await example_manager.add_example_from_interaction(
        input_text="test1",
        output_text="result1"
    )
    example2 = await example_manager.add_example_from_interaction(
        input_text="test2",
        output_text="result2"
    )
    
    # Test default formatting
    formatted = await example_manager.format_examples([example1, example2])
    expected = (
        "Input: test1\n"
        "Output: result1\n"
        "---\n"
        "Input: test2\n"
        "Output: result2\n"
        "---\n"
    )
    assert formatted == expected
    
    # Test custom formatting
    template = "Q: {input_text}\nA: {output_text}\n"
    formatted = await example_manager.format_examples(
        [example1, example2],
        format_template=template
    )
    expected = (
        "Q: test1\n"
        "A: result1\n"
        "Q: test2\n"
        "A: result2\n"
    )
    assert formatted == expected
    
    # Test empty examples
    formatted = await example_manager.format_examples([])
    assert formatted == ""

@pytest.mark.asyncio
async def test_update_example_performance(example_manager: ExampleManager):
    """Test updating example performance metrics."""
    # Add test example
    example = await example_manager.add_example_from_interaction(
        input_text="test",
        output_text="result"
    )
    
    # Update performance - success
    updated = await example_manager.update_example_performance(
        example.example_id,
        success=True,
        metrics={"latency": 0.5}
    )
    assert updated is not None
    assert updated.metadata["performance"]["uses"] == 1
    assert updated.metadata["performance"]["successes"] == 1
    assert updated.metadata["performance"]["metrics"]["latency"] == [0.5]
    
    # Update performance - failure
    updated = await example_manager.update_example_performance(
        example.example_id,
        success=False,
        metrics={"latency": 0.7}
    )
    assert updated is not None
    assert updated.metadata["performance"]["uses"] == 2
    assert updated.metadata["performance"]["successes"] == 1
    assert updated.metadata["performance"]["metrics"]["latency"] == [0.5, 0.7]
    
    # Test non-existent example
    updated = await example_manager.update_example_performance(
        "nonexistent",
        success=True
    )
    assert updated is None 