"""
Unit tests for core utilities.
"""

import pytest

from pepperpy.core.utils import constants, errors


def test_constants():
    """Test core constants."""
    assert isinstance(constants.VERSION, str)
    assert isinstance(constants.API_VERSION, str)
    assert isinstance(constants.DEFAULT_ENCODING, str)
    assert isinstance(constants.DEFAULT_CHUNK_SIZE, int)
    assert isinstance(constants.MAX_RETRIES, int)
    assert isinstance(constants.DEFAULT_TIMEOUT, int)
    assert isinstance(constants.ENABLE_NEW_STRUCTURE, bool)
    assert isinstance(constants.USE_LEGACY_PROVIDER, bool)


def test_error_inheritance():
    """Test error class inheritance."""
    assert issubclass(errors.ConfigurationError, errors.PepperpyError)
    assert issubclass(errors.ValidationError, errors.PepperpyError)
    assert issubclass(errors.ProviderError, errors.PepperpyError)
    assert issubclass(errors.ResourceNotFoundError, errors.PepperpyError)
    assert issubclass(errors.AuthenticationError, errors.PepperpyError)
    assert issubclass(errors.AuthorizationError, errors.PepperpyError)
    assert issubclass(errors.RateLimitError, errors.PepperpyError)
    assert issubclass(errors.TimeoutError, errors.PepperpyError)
    assert issubclass(errors.DependencyError, errors.PepperpyError)


def test_error_instantiation():
    """Test error instantiation."""
    error = errors.PepperpyError("Test error", code="TEST_001")
    assert str(error) == "Test error"
    assert error.code == "TEST_001"
    assert error.message == "Test error"


def test_error_without_code():
    """Test error instantiation without code."""
    error = errors.PepperpyError("Test error")
    assert str(error) == "Test error"
    assert error.code is None
    assert error.message == "Test error"


@pytest.mark.parametrize("error_class", [
    errors.ConfigurationError,
    errors.ValidationError,
    errors.ProviderError,
    errors.ResourceNotFoundError,
    errors.AuthenticationError,
    errors.AuthorizationError,
    errors.RateLimitError,
    errors.TimeoutError,
    errors.DependencyError,
])
def test_specific_errors(error_class):
    """Test specific error classes."""
    error = error_class("Test error", code="TEST_001")
    assert isinstance(error, errors.PepperpyError)
    assert str(error) == "Test error"
    assert error.code == "TEST_001"
    assert error.message == "Test error" 