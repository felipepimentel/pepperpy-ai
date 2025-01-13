"""Tests for exceptions module."""

from pepperpy_ai.exceptions import (
    CapabilityError,
    ConfigurationError,
    DependencyError,
    PepperPyAIError,
    ProviderError,
    ValidationError,
)


def test_base_error() -> None:
    """Test base exception."""
    error = PepperPyAIError("Test error")
    assert str(error) == "Test error"
    assert error.context == {}


def test_configuration_error() -> None:
    """Test configuration error."""
    error = ConfigurationError("Test error", field="test_field")
    assert str(error) == "Test error"
    assert error.context["field"] == "test_field"


def test_provider_error() -> None:
    """Test provider error."""
    error = ProviderError(
        message="Test error",
        provider="test_provider",
        operation="test_operation",
    )
    assert str(error) == "Test error"
    assert error.context["provider"] == "test_provider"
    assert error.context["operation"] == "test_operation"
    assert error.context["cause"] is None


def test_validation_error() -> None:
    """Test validation error."""
    error = ValidationError(
        message="Test error",
        field="test_field",
        value="invalid",
    )
    assert str(error) == "Test error"
    assert error.context["field"] == "test_field"
    assert error.context["value"] == "invalid"


def test_capability_error() -> None:
    """Test capability error."""
    error = CapabilityError(
        message="Test error",
        capability="test_capability",
        operation="test_operation",
    )
    assert str(error) == "Test error"
    assert error.context["capability"] == "test_capability"
    assert error.context["operation"] == "test_operation"
    assert error.context["cause"] is None


def test_dependency_error() -> None:
    """Test dependency error."""
    error = DependencyError(
        feature="Test Feature",
        package="test_package",
        extra="test_extra",
    )

    # Check context
    assert error.context["feature"] == "Test Feature"
    assert error.context["package"] == "test_package"
    assert error.context["extra"] == "test_extra"

    # Check message format
    message = str(error)
    assert "Test Feature" in message
    assert "test_package" in message
    assert "pip install pepperpy-ai[test_extra]" in message
