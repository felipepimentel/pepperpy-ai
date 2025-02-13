"""Tests for the memory CLI module."""

import json
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from pepperpy.cli.memory import MemoryCommands
from pepperpy.memory import MemoryManager


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def memory_cli():
    """Get the memory CLI command group."""
    return MemoryCommands.get_command_group()


@pytest.fixture
def mock_memory_manager(monkeypatch):
    """Mock memory manager for testing."""
    mock = Mock(spec=MemoryManager)
    mock.list_memories.return_value = {
        "vector": [
            {
                "id": "test1",
                "created_at": "2024-03-21",
                "size": 1000,
                "metadata": {"tags": ["test", "example"]},
            }
        ]
    }
    mock.get_memory_info.return_value = {
        "type": "vector",
        "created_at": "2024-03-21",
        "modified_at": "2024-03-21",
        "size": 1000,
        "metadata": {"tags": ["test"]},
        "stats": {"tokens": 100},
    }
    monkeypatch.setattr("pepperpy.cli.memory.MemoryManager", lambda: mock)
    return mock


def test_list_command(runner, memory_cli, mock_memory_manager):
    """Test listing memories."""
    # Test without type filter
    result = runner.invoke(memory_cli, ["list"])
    assert result.exit_code == 0
    assert "test1" in result.output
    assert "2024-03-21" in result.output
    assert "1000 bytes" in result.output
    assert "test, example" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["list", "--type", "vector"])
    assert result.exit_code == 0
    assert "test1" in result.output

    # Test with error
    mock_memory_manager.list_memories.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["list"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_info_command(runner, memory_cli, mock_memory_manager):
    """Test getting memory info."""
    # Test successful info retrieval
    result = runner.invoke(memory_cli, ["info", "test1"])
    assert result.exit_code == 0
    assert "test1" in result.output
    assert "2024-03-21" in result.output
    assert "1000 bytes" in result.output
    assert "test" in result.output

    # Test with error
    mock_memory_manager.get_memory_info.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["info", "test1"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_store_command(runner, memory_cli, mock_memory_manager, tmp_path):
    """Test storing memory content."""
    # Create test content file
    content_file = tmp_path / "content.json"
    content_file.write_text(json.dumps({"test": "data"}))

    # Create test metadata file
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text(json.dumps({"tags": ["test"]}))

    # Test successful store
    result = runner.invoke(
        memory_cli,
        [
            "store",
            "test1",
            "--type",
            "vector",
            "--content",
            str(content_file),
            "--metadata",
            str(metadata_file),
        ],
    )
    assert result.exit_code == 0
    assert "stored successfully" in result.output

    # Test with error
    mock_memory_manager.store.side_effect = Exception("Test error")
    result = runner.invoke(
        memory_cli,
        [
            "store",
            "test1",
            "--type",
            "vector",
            "--content",
            str(content_file),
            "--metadata",
            str(metadata_file),
        ],
    )
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_retrieve_command(runner, memory_cli, mock_memory_manager, tmp_path):
    """Test retrieving memory content."""
    mock_memory_manager.retrieve.return_value = {"test": "data"}

    # Test retrieve to stdout
    result = runner.invoke(memory_cli, ["retrieve", "test1"])
    assert result.exit_code == 0
    assert "test" in result.output
    assert "data" in result.output

    # Test retrieve to file
    output_file = tmp_path / "output.json"
    result = runner.invoke(
        memory_cli, ["retrieve", "test1", "--output", str(output_file)]
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert json.loads(output_file.read_text()) == {"test": "data"}

    # Test with error
    mock_memory_manager.retrieve.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["retrieve", "test1"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_search_command(runner, memory_cli, mock_memory_manager):
    """Test searching memories."""
    mock_memory_manager.search.return_value = [
        Mock(
            score=0.8,
            memory_id="test1",
            memory_type="vector",
            metadata={"tags": ["test"]},
        )
    ]

    # Test basic search
    result = runner.invoke(memory_cli, ["search", "test query"])
    assert result.exit_code == 0
    assert "test1" in result.output
    assert "0.80" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["search", "test query", "--type", "vector"])
    assert result.exit_code == 0
    assert "test1" in result.output

    # Test with error
    mock_memory_manager.search.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["search", "test query"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_delete_command(runner, memory_cli, mock_memory_manager):
    """Test deleting memory."""
    # Test successful delete
    result = runner.invoke(memory_cli, ["delete", "test1"])
    assert result.exit_code == 0
    assert "deleted successfully" in result.output

    # Test with error
    mock_memory_manager.delete.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["delete", "test1"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_clear_command(runner, memory_cli, mock_memory_manager):
    """Test clearing memories."""
    # Test with confirmation
    result = runner.invoke(memory_cli, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "Cleared all memories" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["clear", "--type", "vector"], input="y\n")
    assert result.exit_code == 0
    assert "Cleared all memories of type vector" in result.output

    # Test without confirmation
    result = runner.invoke(memory_cli, ["clear"], input="n\n")
    assert result.exit_code == 0
    assert "Cleared all memories" not in result.output


@pytest.mark.asyncio
async def test_stats_command(runner, memory_cli, mock_memory_manager):
    """Test showing memory statistics."""
    mock_memory_manager.get_memory_stats.return_value = {
        "usage": {
            "total_size": 1000,
            "item_count": 10,
        },
        "operations": {
            "reads": 100,
            "writes": 50,
        },
        "performance": {
            "avg_latency": "10ms",
        },
    }

    # Test basic stats
    result = runner.invoke(memory_cli, ["stats"])
    assert result.exit_code == 0
    assert "1000 bytes" in result.output
    assert "10" in result.output
    assert "100" in result.output
    assert "50" in result.output
    assert "10ms" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["stats", "--type", "vector"])
    assert result.exit_code == 0

    # Test with error
    mock_memory_manager.get_memory_stats.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["stats"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_backup_command(runner, memory_cli, mock_memory_manager, tmp_path):
    """Test creating memory backup."""
    backup_path = tmp_path / "backup.zip"

    # Test successful backup
    result = runner.invoke(memory_cli, ["backup", str(backup_path)])
    assert result.exit_code == 0
    assert "Backup created successfully" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["backup", str(backup_path), "--type", "vector"])
    assert result.exit_code == 0

    # Test with error
    mock_memory_manager.create_backup.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["backup", str(backup_path)])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_restore_command(runner, memory_cli, mock_memory_manager, tmp_path):
    """Test restoring memory backup."""
    backup_path = tmp_path / "backup.zip"
    backup_path.touch()

    # Test with confirmation
    result = runner.invoke(memory_cli, ["restore", str(backup_path)], input="y\n")
    assert result.exit_code == 0
    assert "Memories restored successfully" in result.output

    # Test with type filter
    result = runner.invoke(
        memory_cli, ["restore", str(backup_path), "--type", "vector"], input="y\n"
    )
    assert result.exit_code == 0

    # Test without confirmation
    result = runner.invoke(memory_cli, ["restore", str(backup_path)], input="n\n")
    assert result.exit_code == 0
    assert "Memories restored successfully" not in result.output

    # Test with error
    mock_memory_manager.restore_backup.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["restore", str(backup_path)], input="y\n")
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_optimize_command(runner, memory_cli, mock_memory_manager):
    """Test optimizing memory storage."""
    mock_memory_manager.optimize.return_value = {
        "space_saved": 1000,
        "time_taken": 1.5,
        "details": {
            "items_processed": 100,
            "compression_ratio": "2:1",
        },
    }

    # Test basic optimize
    result = runner.invoke(memory_cli, ["optimize"])
    assert result.exit_code == 0
    assert "1000 bytes" in result.output
    assert "1.50s" in result.output
    assert "100" in result.output
    assert "2:1" in result.output

    # Test with type filter
    result = runner.invoke(memory_cli, ["optimize", "--type", "vector"])
    assert result.exit_code == 0

    # Test with error
    mock_memory_manager.optimize.side_effect = Exception("Test error")
    result = runner.invoke(memory_cli, ["optimize"])
    assert result.exit_code == 0
    assert "Error: Test error" in result.output
