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
    error = DependencyError(
        feature="Test Feature",
        package="test_package",
        extra="test_extra"
    )
    
    # Check attributes
    assert error.feature == "Test Feature"
    assert error.package == "test_package"
    assert error.extra == "test_extra"
    
    # Check message format
    message = str(error)
    assert "Test Feature" in message
    assert "test_package" in message
    assert "pip install pepperpy-ai[test_extra]" in message
    assert "poetry add pepperpy-ai[test_extra]" in message
