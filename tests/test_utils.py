"""Tests for utilities module."""

import pytest
from pepperpy_ai.utils.dependencies import get_module_version, is_package_installed
from pepperpy_ai.utils.config import load_module_config, validate_module_config


def test_get_module_version() -> None:
    """Test getting module version."""
    version = get_module_version("pytest")
    assert isinstance(version, str)
    assert len(version) > 0


def test_is_package_installed() -> None:
    """Test checking if package is installed."""
    assert is_package_installed("pytest")
    assert not is_package_installed("nonexistent_package")


def test_load_module_config() -> None:
    """Test loading module configuration."""
    config = load_module_config("test_module")
    assert isinstance(config, dict)


def test_validate_module_config() -> None:
    """Test validating module configuration."""
    config = {"name": "test", "version": "1.0.0", "enabled": True}
    assert validate_module_config(config) is None
