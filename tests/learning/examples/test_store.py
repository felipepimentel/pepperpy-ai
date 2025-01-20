"""Tests for example store functionality."""

import pytest
from datetime import datetime
from pathlib import Path

from pepperpy.learning.examples import Example, ExampleStore

@pytest.mark.asyncio
async def test_add_example(example_store: ExampleStore):
    """Test adding an example to the store."""
    example = example_store.add_example(
        input_text="test input",
        output_text="test output",
        example_id="test1",
        tags={"tag1", "tag2"},
        metadata={"source": "test"}
    )
    
    assert example.input_text == "test input"
    assert example.output_text == "test output"
    assert example.example_id == "test1"
    assert example.tags == {"tag1", "tag2"}
    assert example.metadata == {"source": "test"}
    assert isinstance(example.created_at, datetime)
    assert isinstance(example.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_example(example_store: ExampleStore):
    """Test retrieving an example from the store."""
    # Add example
    example_store.add_example(
        input_text="test input",
        output_text="test output",
        example_id="test1"
    )
    
    # Retrieve example
    example = example_store.get_example("test1")
    assert example is not None
    assert example.input_text == "test input"
    assert example.output_text == "test output"
    
    # Test non-existent example
    assert example_store.get_example("nonexistent") is None

@pytest.mark.asyncio
async def test_update_example(example_store: ExampleStore):
    """Test updating an example in the store."""
    # Add example
    example_store.add_example(
        input_text="test input",
        output_text="test output",
        example_id="test1",
        tags={"tag1"},
        metadata={"source": "test"}
    )
    
    # Update example
    updated = example_store.update_example(
        example_id="test1",
        input_text="new input",
        tags={"tag2", "tag3"},
        metadata={"source": "updated"}
    )
    
    assert updated is not None
    assert updated.input_text == "new input"
    assert updated.output_text == "test output"  # Unchanged
    assert updated.tags == {"tag2", "tag3"}
    assert updated.metadata == {"source": "updated"}
    assert updated.updated_at > updated.created_at

@pytest.mark.asyncio
async def test_delete_example(example_store: ExampleStore):
    """Test deleting an example from the store."""
    # Add example
    example_store.add_example(
        input_text="test input",
        output_text="test output",
        example_id="test1",
        tags={"tag1"}
    )
    
    # Delete example
    assert example_store.delete_example("test1") is True
    assert example_store.get_example("test1") is None
    assert example_store.delete_example("test1") is False

@pytest.mark.asyncio
async def test_find_by_tags(example_store: ExampleStore):
    """Test finding examples by tags."""
    # Add examples with different tags
    example_store.add_example(
        input_text="test1",
        output_text="output1",
        example_id="1",
        tags={"tag1", "tag2"}
    )
    example_store.add_example(
        input_text="test2",
        output_text="output2",
        example_id="2",
        tags={"tag2", "tag3"}
    )
    example_store.add_example(
        input_text="test3",
        output_text="output3",
        example_id="3",
        tags={"tag3", "tag4"}
    )
    
    # Test finding with single tag
    results = example_store.find_by_tags({"tag1"})
    assert len(results) == 1
    assert results[0].example_id == "1"
    
    # Test finding with multiple tags (require all)
    results = example_store.find_by_tags({"tag2", "tag3"}, require_all=True)
    assert len(results) == 1
    assert results[0].example_id == "2"
    
    # Test finding with multiple tags (any)
    results = example_store.find_by_tags({"tag1", "tag4"}, require_all=False)
    assert len(results) == 2
    assert {r.example_id for r in results} == {"1", "3"}

@pytest.mark.asyncio
async def test_save_and_load(example_store: ExampleStore, temp_dir: Path):
    """Test saving and loading examples."""
    # Add examples
    example_store.add_example(
        input_text="test1",
        output_text="output1",
        example_id="1",
        tags={"tag1"}
    )
    example_store.add_example(
        input_text="test2",
        output_text="output2",
        example_id="2",
        tags={"tag2"}
    )
    
    # Save examples
    save_path = temp_dir / "test_save.json"
    example_store.save(save_path)
    
    # Create new store and load examples
    new_store = ExampleStore(storage_dir=temp_dir)
    new_store.load(save_path)
    
    # Verify loaded examples
    example1 = new_store.get_example("1")
    assert example1 is not None
    assert example1.input_text == "test1"
    assert example1.tags == {"tag1"}
    
    example2 = new_store.get_example("2")
    assert example2 is not None
    assert example2.input_text == "test2"
    assert example2.tags == {"tag2"} 