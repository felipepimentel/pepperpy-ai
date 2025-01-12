"""Tests for exceptions module."""

import pytest
from pepperpy_ai.exceptions import (
    PepperPyAIError,
    ConfigurationError,
    ProviderError,
    ValidationError,
    CapabilityError,
    DependencyError,
)


def test_base_error() -> None:
    """Test base exception."""
    error = PepperPyAIError("Test error")
    assert str(error) == "Test error"


def test_configuration_error() -> None:
    """Test configuration error."""
    error = ConfigurationError("Test error", field="test_field")
    assert str(error) == "Test error"
    assert error.field == "test_field"


def test_provider_error() -> None:
    """Test provider error."""
    error = ProviderError("Test error", provider="test_provider")
    assert str(error) == "Test error"
    assert error.provider == "test_provider"


def test_validation_error() -> None:
    """Test validation error."""
    error = ValidationError("Test error", field="test_field", value="invalid")
    assert str(error) == "Test error"
    assert error.field == "test_field"
    assert error.value == "invalid"


def test_capability_error() -> None:
    """Test capability error."""
    error = CapabilityError("Test error", capability="test_capability")
    assert str(error) == "Test error"
    assert error.capability == "test_capability"


def test_dependency_error() -> None:
    """Test dependency error."""
    error = DependencyError("Test error", package="test_package")
    assert str(error) == "Test error"
    assert error.package == "test_package"
