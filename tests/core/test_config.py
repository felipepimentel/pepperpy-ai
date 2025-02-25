"""Tests for the configuration system."""

from pathlib import Path

import pytest

from pepperpy.core.config import (
    ConfigManager,
    ConfigModel,
    EnvironmentProvider,
    FilesystemProvider,
)


class TestConfig(ConfigModel):
    """Test configuration model."""

    debug: bool = False
    host: str = "localhost"
    port: int = 8000
    data_dir: Path | None = None
    tags: list[str] = []


@pytest.fixture
def config_dir(tmp_path):
    """Create temporary configuration directory."""
    return tmp_path / "config"


@pytest.fixture
def env_provider():
    """Create environment provider."""
    return EnvironmentProvider(prefix="TEST_")


@pytest.fixture
def fs_provider(config_dir):
    """Create filesystem provider."""
    return FilesystemProvider(config_dir)


@pytest.fixture
def config_manager(env_provider, fs_provider):
    """Create configuration manager."""
    manager = ConfigManager()
    manager.add_provider(env_provider)
    manager.add_provider(fs_provider)
    return manager


class TestConfigModel:
    """Tests for ConfigModel."""

    def test_from_env(self, monkeypatch):
        """Test loading from environment variables."""
        # Set environment variables
        monkeypatch.setenv("PEPPERPY_DEBUG", "true")
        monkeypatch.setenv("PEPPERPY_HOST", "example.com")
        monkeypatch.setenv("PEPPERPY_PORT", "9000")
        monkeypatch.setenv("PEPPERPY_DATA_DIR", "/data")
        monkeypatch.setenv("PEPPERPY_TAGS", "tag1,tag2,tag3")

        # Load configuration
        config = TestConfig.from_env()

        # Check values
        assert config.debug is True
        assert config.host == "example.com"
        assert config.port == 9000
        assert config.data_dir == Path("/data")
        assert config.tags == ["tag1", "tag2", "tag3"]

    def test_from_file(self, tmp_path):
        """Test loading from configuration file."""
        # Create configuration file
        config_file = tmp_path / "config.json"
        config_file.write_text(
            """{
                "debug": true,
                "host": "example.com",
                "port": 9000,
                "data_dir": "/data",
                "tags": ["tag1", "tag2", "tag3"]
            }"""
        )

        # Load configuration
        config = TestConfig.from_file(config_file)

        # Check values
        assert config.debug is True
        assert config.host == "example.com"
        assert config.port == 9000
        assert config.data_dir == Path("/data")
        assert config.tags == ["tag1", "tag2", "tag3"]

    def test_to_file(self, tmp_path):
        """Test saving to configuration file."""
        # Create configuration
        config = TestConfig(
            debug=True,
            host="example.com",
            port=9000,
            data_dir=Path("/data"),
            tags=["tag1", "tag2", "tag3"],
        )

        # Save configuration
        config_file = tmp_path / "config.json"
        config.to_file(config_file)

        # Load and check values
        loaded = TestConfig.from_file(config_file)
        assert loaded.debug == config.debug
        assert loaded.host == config.host
        assert loaded.port == config.port
        assert loaded.data_dir == config.data_dir
        assert loaded.tags == config.tags


class TestEnvironmentProvider:
    """Tests for EnvironmentProvider."""

    async def test_get(self, env_provider, monkeypatch):
        """Test getting values."""
        # Set environment variables
        monkeypatch.setenv("TEST_FOO", "bar")
        monkeypatch.setenv("TEST_BAZ_QUX", "123")

        # Get values
        assert await env_provider.get("foo") == "bar"
        assert await env_provider.get("baz/qux") == "123"
        assert await env_provider.get("missing") is None

    async def test_list(self, env_provider, monkeypatch):
        """Test listing keys."""
        # Set environment variables
        monkeypatch.setenv("TEST_FOO", "bar")
        monkeypatch.setenv("TEST_BAZ_QUX", "123")
        monkeypatch.setenv("OTHER_VAR", "456")

        # List keys
        keys = await env_provider.list()
        assert sorted(keys) == ["baz/qux", "foo"]

        # List with prefix
        keys = await env_provider.list("baz")
        assert keys == ["baz/qux"]

    async def test_set(self, env_provider):
        """Test setting values."""
        with pytest.raises(NotImplementedError):
            await env_provider.set("foo", "bar")

    async def test_delete(self, env_provider):
        """Test deleting values."""
        with pytest.raises(NotImplementedError):
            await env_provider.delete("foo")


class TestFilesystemProvider:
    """Tests for FilesystemProvider."""

    async def test_get(self, fs_provider):
        """Test getting values."""
        # Set values
        await fs_provider.set("foo", "bar")
        await fs_provider.set("baz/qux", "123")

        # Get values
        assert await fs_provider.get("foo") == "bar"
        assert await fs_provider.get("baz/qux") == "123"
        assert await fs_provider.get("missing") is None

    async def test_set(self, fs_provider):
        """Test setting values."""
        # Set values
        await fs_provider.set("foo", "bar")
        await fs_provider.set("baz/qux", "123")

        # Check files
        assert (fs_provider.directory / "foo.json").exists()
        assert (fs_provider.directory / "baz_qux.json").exists()

        # Check content
        with (fs_provider.directory / "foo.json").open() as f:
            assert f.read() == '{\n  "value": "bar"\n}'

    async def test_delete(self, fs_provider):
        """Test deleting values."""
        # Set value
        await fs_provider.set("foo", "bar")
        assert await fs_provider.get("foo") == "bar"

        # Delete value
        await fs_provider.delete("foo")
        assert await fs_provider.get("foo") is None
        assert not (fs_provider.directory / "foo.json").exists()

    async def test_list(self, fs_provider):
        """Test listing keys."""
        # Set values
        await fs_provider.set("foo", "bar")
        await fs_provider.set("baz/qux", "123")

        # List keys
        keys = await fs_provider.list()
        assert sorted(keys) == ["baz/qux", "foo"]

        # List with prefix
        keys = await fs_provider.list("baz")
        assert keys == ["baz/qux"]


class TestConfigManager:
    """Tests for ConfigManager."""

    async def test_get(self, config_manager, monkeypatch):
        """Test getting values."""
        # Set values in both providers
        monkeypatch.setenv("TEST_FOO", "from_env")
        await config_manager._providers[1].set("foo", "from_fs")

        # Environment provider should take precedence
        assert await config_manager.get("foo") == "from_env"

        # Fall back to filesystem provider
        assert await config_manager.get("bar") is None
        await config_manager._providers[1].set("bar", "from_fs")
        assert await config_manager.get("bar") == "from_fs"

    async def test_set(self, config_manager):
        """Test setting values."""
        # Set value
        await config_manager.set("foo", "bar")

        # Should be set in all providers that support it
        assert await config_manager._providers[1].get("foo") == "bar"

    async def test_delete(self, config_manager):
        """Test deleting values."""
        # Set value
        await config_manager.set("foo", "bar")
        assert await config_manager.get("foo") == "bar"

        # Delete value
        await config_manager.delete("foo")
        assert await config_manager.get("foo") is None

    async def test_list(self, config_manager, monkeypatch):
        """Test listing keys."""
        # Set values in both providers
        monkeypatch.setenv("TEST_FOO", "from_env")
        monkeypatch.setenv("TEST_BAR", "from_env")
        await config_manager._providers[1].set("baz", "from_fs")
        await config_manager._providers[1].set("qux", "from_fs")

        # List all keys
        keys = await config_manager.list()
        assert sorted(keys) == ["bar", "baz", "foo", "qux"]

        # List with prefix
        keys = await config_manager.list("ba")
        assert sorted(keys) == ["bar", "baz"]
