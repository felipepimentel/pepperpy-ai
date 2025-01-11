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


def test_base_exception():
    """Test base exception."""
    msg = "Test error"
    exc = PepperPyAIError(msg)
    assert str(exc) == msg


def test_configuration_error():
    """Test configuration error."""
    msg = "Invalid config"
    field = "api_key"
    exc = ConfigurationError(msg, field)
    assert str(exc) == msg
    assert exc.field == field


def test_provider_error():
    """Test provider error."""
    msg = "Provider failed"
    provider = "test_provider"
    exc = ProviderError(msg, provider)
    assert str(exc) == msg
    assert exc.provider == provider


def test_validation_error():
    """Test validation error."""
    msg = "Invalid value"
    field = "temperature"
    value = 2.0
    exc = ValidationError(msg, field, value)
    assert str(exc) == msg
    assert exc.field == field
    assert exc.value == value


def test_capability_error():
    """Test capability error."""
    msg = "Capability not found"
    capability = "rag"
    exc = CapabilityError(msg, capability)
    assert str(exc) == msg
    assert exc.capability == capability


def test_dependency_error():
    """Test dependency error."""
    msg = "Missing package"
    package = "openai"
    exc = DependencyError(msg, package)
    assert str(exc) == msg
    assert exc.package == package 