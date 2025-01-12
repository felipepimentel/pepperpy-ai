"""Tests for utility functions."""

import pytest

from pepperpy_ai.exceptions import DependencyError
from pepperpy_ai.utils import (
    check_dependency,
    format_exception,
    get_missing_dependencies,
    merge_configs,
    safe_import,
    verify_dependencies,
)


def test_check_dependency() -> None:
    """Test check_dependency function."""
    assert check_dependency("pytest") is True
    assert check_dependency("nonexistent_package") is False


def test_safe_import() -> None:
    """Test safe_import function."""
    pytest = safe_import("pytest", "main")
    assert pytest is not None
    assert safe_import("nonexistent_package", "main") is None


def test_get_missing_dependencies() -> None:
    """Test get_missing_dependencies function."""
    deps = ["pytest", "nonexistent_package"]
    missing = get_missing_dependencies(deps)
    assert "nonexistent_package" in missing
    assert "pytest" not in missing


def test_verify_dependencies() -> None:
    """Test verify_dependencies function."""
    deps = ["pytest"]
    verify_dependencies("test", deps)  # Should not raise
    deps = ["nonexistent_package"]
    with pytest.raises(DependencyError):
        verify_dependencies("test", deps)


def test_merge_configs() -> None:
    """Test merge_configs function."""
    config1 = {"a": 1, "b": 2}
    config2 = {"b": 3, "c": 4}
    merged = merge_configs(config1, config2)
    assert merged == {"a": 1, "b": 3, "c": 4}


def test_format_exception() -> None:
    """Test format_exception function."""
    try:
        raise ValueError("test error")
    except ValueError as e:
        formatted = format_exception(e)
        assert "ValueError" in formatted
        assert "test error" in formatted
