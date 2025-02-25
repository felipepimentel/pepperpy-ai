"""Tests for environment configuration module."""

import os

import pytest

from pepperpy.core.config.env import EnvConfigProvider


@pytest.fixture
def env_vars() -> dict[str, str]:
    """Environment variables fixture."""
    return {
        "PEPPERPY_DATABASE_URL": "postgresql://localhost:5432/db",
        "PEPPERPY_DATABASE_PORT": "5432",
        "PEPPERPY_DEBUG": "true",
        "PEPPERPY_API_VERSION": "1.0",
        "PEPPERPY_ALLOWED_HOSTS": "[localhost, 127.0.0.1]",
        "PEPPERPY_RATE_LIMIT": "10.5",
        "OTHER_VAR": "ignored",
    }


@pytest.fixture
def env_provider(env_vars: dict[str, str]) -> EnvConfigProvider:
    """Environment configuration provider fixture."""
    # Save current environment
    old_environ = dict(os.environ)

    # Update environment with test variables
    os.environ.update(env_vars)

    # Create provider
    provider = EnvConfigProvider()

    yield provider

    # Restore environment
    os.environ.clear()
    os.environ.update(old_environ)


def test_env_provider_init(env_provider: EnvConfigProvider):
    """Test environment provider initialization."""
    # Test default values
    assert env_provider._prefix == "PEPPERPY"
    assert env_provider._separator == "_"
    assert env_provider._lowercase is True

    # Test custom initialization
    provider = EnvConfigProvider(prefix="TEST", separator="-", lowercase=False)
    assert provider._prefix == "TEST"
    assert provider._separator == "-"
    assert provider._lowercase is False


def test_env_provider_get(env_provider: EnvConfigProvider):
    """Test getting configuration values."""
    # Test string value
    assert env_provider.get("database.url") == "postgresql://localhost:5432/db"

    # Test integer value
    assert env_provider.get("database.port") == 5432

    # Test boolean value
    assert env_provider.get("debug") is True

    # Test float value
    assert env_provider.get("api.version") == 1.0

    # Test list value
    assert env_provider.get("allowed.hosts") == ["localhost", "127.0.0.1"]

    # Test decimal value
    assert env_provider.get("rate.limit") == 10.5

    # Test nonexistent value
    assert env_provider.get("nonexistent") is None


def test_env_provider_set(env_provider: EnvConfigProvider):
    """Test setting configuration values."""
    # Test setting new value
    env_provider.set("new.key", "value")
    assert env_provider.get("new.key") == "value"

    # Test overwriting existing value
    env_provider.set("database.url", "new_url")
    assert env_provider.get("database.url") == "new_url"


def test_env_provider_delete(env_provider: EnvConfigProvider):
    """Test deleting configuration values."""
    # Test deleting existing value
    env_provider.delete("database.url")
    assert env_provider.get("database.url") is None

    # Test deleting nonexistent value
    env_provider.delete("nonexistent")  # Should not raise error


def test_env_provider_exists(env_provider: EnvConfigProvider):
    """Test checking configuration value existence."""
    assert env_provider.exists("database.url")
    assert not env_provider.exists("nonexistent")


def test_env_provider_clear(env_provider: EnvConfigProvider):
    """Test clearing configuration values."""
    # Add custom value
    env_provider.set("custom.key", "value")

    # Clear provider
    env_provider.clear()

    # Test that environment values are reloaded
    assert env_provider.get("database.url") == "postgresql://localhost:5432/db"
    assert env_provider.get("custom.key") is None


def test_env_provider_case_sensitivity():
    """Test case sensitivity handling."""
    # Save current environment
    old_environ = dict(os.environ)

    try:
        # Set test environment variables
        os.environ.update({
            "PEPPERPY_MIXED_CASE_KEY": "value",
            "PEPPERPY_lowercase_key": "value2",
        })

        # Test with lowercase=True (default)
        provider = EnvConfigProvider()
        assert provider.get("mixed.case.key") == "value"
        assert provider.get("lowercase.key") == "value2"

        # Test with lowercase=False
        provider = EnvConfigProvider(lowercase=False)
        assert provider.get("MIXED_CASE_KEY") == "value"
        assert provider.get("lowercase_key") == "value2"

    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(old_environ)


def test_env_provider_value_conversion():
    """Test value type conversion."""
    # Save current environment
    old_environ = dict(os.environ)

    try:
        # Set test environment variables
        os.environ.update({
            "PEPPERPY_STRING": "value",
            "PEPPERPY_INTEGER": "42",
            "PEPPERPY_FLOAT": "3.14",
            "PEPPERPY_BOOL_TRUE": "true",
            "PEPPERPY_BOOL_FALSE": "false",
            "PEPPERPY_LIST": "[1, 2, 3]",
            "PEPPERPY_MIXED_LIST": "[true, 42, 3.14, string]",
        })

        provider = EnvConfigProvider()

        # Test string conversion
        assert provider.get("string") == "value"

        # Test integer conversion
        assert provider.get("integer") == 42
        assert isinstance(provider.get("integer"), int)

        # Test float conversion
        assert provider.get("float") == 3.14
        assert isinstance(provider.get("float"), float)

        # Test boolean conversion
        assert provider.get("bool.true") is True
        assert provider.get("bool.false") is False

        # Test list conversion
        assert provider.get("list") == [1, 2, 3]

        # Test mixed list conversion
        assert provider.get("mixed.list") == [True, 42, 3.14, "string"]

    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(old_environ)


if __name__ == "__main__":
    pytest.main([__file__])
