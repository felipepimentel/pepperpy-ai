"""Test utilities module."""

import pytest

from pepperpy.exceptions import DependencyError
from pepperpy.utils.dependencies import (
    check_dependency,
    get_missing_dependencies,
    verify_dependencies,
)
from pepperpy.utils.exceptions import format_exception


def test_check_dependency() -> None:
    """Test check_dependency function."""
    assert check_dependency("pytest")
    assert not check_dependency("nonexistent_package")


def test_get_missing_dependencies() -> None:
    """Test get_missing_dependencies function."""
    dependencies = ["pytest", "nonexistent_package"]
    missing = get_missing_dependencies(dependencies)
    assert "nonexistent_package" in missing
    assert "pytest" not in missing


def test_verify_dependencies() -> None:
    """Test verify_dependencies function."""
    verify_dependencies(["pytest"])

    with pytest.raises(DependencyError):
        verify_dependencies(["nonexistent_package"])


def test_format_exception() -> None:
    """Test format_exception function."""
    try:
        raise ValueError("test error")
    except ValueError as e:
        error_str = format_exception(e)
        assert "ValueError" in error_str
        assert "test error" in error_str
