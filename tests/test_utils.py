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


def test_check_dependency():
    """Test check_dependency function."""
    assert check_dependency("pytest")  # Should be installed
    assert not check_dependency("nonexistent_package")


def test_get_missing_dependencies():
    """Test get_missing_dependencies function."""
    required = ["pytest", "nonexistent_package"]
    missing = get_missing_dependencies(required)
    assert missing == ["nonexistent_package"]


def test_verify_dependencies():
    """Test verify_dependencies function."""
    # Should not raise for installed packages
    verify_dependencies("test", ["pytest"])

    # Should raise for missing packages
    with pytest.raises(DependencyError) as exc_info:
        verify_dependencies("test", ["nonexistent_package"])
    assert "nonexistent_package" in str(exc_info.value)


def test_safe_import():
    """Test safe_import function."""
    # Test successful import
    cls = safe_import("pepperpy_ai.exceptions", "DependencyError")
    assert cls == DependencyError

    # Test failed import
    cls = safe_import("nonexistent_module", "NonexistentClass")
    assert cls is None

    # Test base class verification
    class BaseClass:
        pass

    cls = safe_import("pepperpy_ai.exceptions", "DependencyError", BaseClass)
    assert cls is None


def test_merge_configs():
    """Test merge_configs function."""
    base = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3,
        },
    }
    override = {
        "b": {
            "d": 4,
            "e": 5,
        },
        "f": 6,
    }
    result = merge_configs(base, override)
    assert result == {
        "a": 1,
        "b": {
            "c": 2,
            "d": 4,
            "e": 5,
        },
        "f": 6,
    }


def test_format_exception():
    """Test format_exception function."""
    exc = ValueError("test error")
    formatted = format_exception(exc)
    assert formatted == "ValueError: test error" 