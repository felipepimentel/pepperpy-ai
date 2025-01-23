"""Tests for utility functions."""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from pepperpy.core.utils.helpers import (
    ensure_directory,
    load_json,
    save_json,
    generate_uuid,
    generate_timestamp,
    calculate_hash,
    chunk_list,
    merge_dicts,
    safe_get,
    format_size,
    parse_size,
)

def test_ensure_directory():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        result = ensure_directory(test_dir)
        assert result == test_dir
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_json_operations():
    """Test JSON file operations."""
    test_data = {"key": "value", "number": 42}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.json"
        
        # Test save
        save_json(test_data, test_file)
        assert test_file.exists()
        
        # Test load
        loaded_data = load_json(test_file)
        assert loaded_data == test_data

def test_generate_uuid():
    """Test UUID generation."""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    assert isinstance(uuid1, str)
    assert len(uuid1) == 36  # Standard UUID length
    assert uuid1 != uuid2  # Should be unique

def test_generate_timestamp():
    """Test timestamp generation."""
    timestamp = generate_timestamp()
    assert isinstance(timestamp, str)
    # Should be parseable as ISO format
    datetime.fromisoformat(timestamp)

def test_calculate_hash():
    """Test hash calculation."""
    test_str = "test string"
    test_bytes = b"test bytes"
    
    # Test string input
    hash1 = calculate_hash(test_str)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 length
    
    # Test bytes input
    hash2 = calculate_hash(test_bytes)
    assert isinstance(hash2, str)
    assert len(hash2) == 64

def test_chunk_list():
    """Test list chunking."""
    test_list = list(range(10))
    
    # Test with exact chunks
    chunks = chunk_list(test_list, 2)
    assert len(chunks) == 5
    assert all(len(chunk) == 2 for chunk in chunks)
    
    # Test with remainder
    chunks = chunk_list(test_list, 3)
    assert len(chunks) == 4
    assert len(chunks[-1]) == 1

def test_merge_dicts():
    """Test dictionary merging."""
    dict1 = {
        "a": 1,
        "b": {"x": 1, "y": 2},
        "c": [1, 2, 3]
    }
    dict2 = {
        "b": {"y": 3, "z": 4},
        "d": 4
    }
    
    result = merge_dicts(dict1, dict2)
    assert result["a"] == 1
    assert result["b"] == {"x": 1, "y": 3, "z": 4}
    assert result["c"] == [1, 2, 3]
    assert result["d"] == 4

def test_safe_get():
    """Test safe dictionary access."""
    test_dict = {
        "a": {
            "b": {
                "c": 42
            }
        }
    }
    
    # Test existing path
    assert safe_get(test_dict, "a.b.c") == 42
    
    # Test missing path
    assert safe_get(test_dict, "a.b.d") is None
    assert safe_get(test_dict, "x.y.z", default=123) == 123

def test_format_size():
    """Test size formatting."""
    # Test various sizes
    assert format_size(500) == "500.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1024 * 1024) == "1.00 MB"
    assert format_size(1024 * 1024 * 1024) == "1.00 GB"

def test_parse_size():
    """Test size parsing."""
    # Test various formats
    assert parse_size("500B") == 500
    assert parse_size("1KB") == 1024
    assert parse_size("1MB") == 1024 * 1024
    assert parse_size("1GB") == 1024 * 1024 * 1024
    
    # Test with decimals
    assert parse_size("1.5KB") == round(1.5 * 1024)
    
    # Test invalid formats
    with pytest.raises(ValueError):
        parse_size("invalid") 