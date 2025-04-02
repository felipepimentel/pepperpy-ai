"""Integration tests for the plugin system."""

from typing import List, Optional

import pytest

from pepperpy.plugins.manager import (
    create_and_initialize_provider,
    get_plugin_manager,
)
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.registry import (
    clear_path_cache,
    create_provider_instance,
    register_plugin,
    register_plugin_alias,
    register_plugin_fallbacks,
)


# Sample plugin classes for testing
class BaseTestPlugin(PepperpyPlugin):
    """Base test plugin for integration testing."""

    initialized_plugins: List[str] = []
    cleaned_up_plugins: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plugin_id = f"{self.__class__.__name__}"

    async def initialize(self):
        """Initialize the plugin."""
        if self.initialized:
            return

        self.__class__.initialized_plugins.append(self.plugin_id)
        self.initialized = True

    async def cleanup(self):
        """Clean up the plugin."""
        if not self.initialized:
            return

        self.__class__.cleaned_up_plugins.append(self.plugin_id)
        self.initialized = False


class DatabasePlugin(BaseTestPlugin):
    """Sample database plugin."""

    host: str = "localhost"
    port: int = 5432
    username: str = "user"
    password: str = "password"

    async def initialize(self):
        """Initialize database connection."""
        await super().initialize()
        self.db_connection = f"Connected to {self.host}:{self.port}"

    async def cleanup(self):
        """Close database connection."""
        await super().cleanup()
        del self.db_connection


class CachePlugin(BaseTestPlugin):
    """Sample cache plugin."""

    host: str = "localhost"
    port: int = 6379

    async def initialize(self):
        """Initialize cache connection."""
        await super().initialize()
        self.cache_connection = f"Connected to {self.host}:{self.port}"

    async def cleanup(self):
        """Close cache connection."""
        await super().cleanup()
        del self.cache_connection


class APIPlugin(BaseTestPlugin):
    """Sample API plugin with dependencies."""

    url: str = "https://api.example.com"
    api_key: Optional[str] = None

    async def initialize(self):
        """Initialize API connection."""
        await super().initialize()
        self.api_connection = f"Connected to {self.url}"

    async def cleanup(self):
        """Close API connection."""
        await super().cleanup()
        del self.api_connection


@pytest.fixture
def reset_plugin_system():
    """Reset the plugin system before each test."""
    # Reset the plugin registry
    from pepperpy.plugins.registry import (
        _plugin_aliases,
        _plugin_fallbacks,
        _plugin_metadata,
        _plugin_paths,
        _plugin_registry,
    )

    _plugin_registry.clear()
    _plugin_metadata.clear()
    _plugin_paths.clear()
    _plugin_aliases.clear()
    _plugin_fallbacks.clear()
    clear_path_cache()

    # Reset the plugin manager
    import pepperpy.plugins.manager

    pepperpy.plugins.manager._plugin_manager = None

    # Reset plugin tracking
    BaseTestPlugin.initialized_plugins = []
    BaseTestPlugin.cleaned_up_plugins = []

    yield


@pytest.mark.asyncio
async def test_registration_and_initialization(reset_plugin_system):
    """Test registering, creating, and initializing plugins."""
    # Register plugins
    register_plugin("db", "postgres", DatabasePlugin)
    register_plugin("cache", "redis", CachePlugin)
    register_plugin("api", "rest", APIPlugin)

    # Create and initialize a provider
    db = await create_and_initialize_provider("db", "postgres", host="db.example.com")

    # Check provider is created and initialized
    assert db.initialized
    assert db.host == "db.example.com"
    assert "DatabasePlugin" in BaseTestPlugin.initialized_plugins

    # Create another provider manually
    cache = create_provider_instance("cache", "redis", port=1234)

    # It shouldn't be initialized yet
    assert not cache.initialized
    assert cache.port == 1234

    # Initialize it
    await cache.initialize()

    # Now it should be initialized
    assert cache.initialized
    assert "CachePlugin" in BaseTestPlugin.initialized_plugins

    # Clean up
    await db.cleanup()
    await cache.cleanup()

    # Check cleanup occurred in the right order
    assert BaseTestPlugin.cleaned_up_plugins == ["DatabasePlugin", "CachePlugin"]


@pytest.mark.asyncio
async def test_dependencies_and_lifecycle(reset_plugin_system):
    """Test plugin dependencies and lifecycle management."""
    # Register plugins
    register_plugin("db", "postgres", DatabasePlugin)
    register_plugin("cache", "redis", CachePlugin)
    register_plugin("api", "rest", APIPlugin)

    # Register dependencies
    manager = get_plugin_manager()
    manager.register_plugin_metadata(
        "api",
        "rest",
        {
            "dependencies": [
                {"type": "db", "provider": "postgres"},
                {"type": "cache", "provider": "redis", "dependency_type": "optional"},
            ]
        },
    )

    # Create API provider
    api = manager.create_instance("api", "rest")

    # Dependencies shouldn't be loaded yet
    assert manager.get_instance("db", "postgres") is None
    assert manager.get_instance("cache", "redis") is None

    # Load dependencies
    dependencies = await manager.load_dependencies("api", "rest")

    # Check dependencies are loaded
    assert len(dependencies) == 2
    assert ("db", "postgres") in dependencies
    assert ("cache", "redis") in dependencies

    # Check instances are created and initialized
    db = manager.get_instance("db", "postgres")
    cache = manager.get_instance("cache", "redis")

    assert db is not None
    assert cache is not None
    assert db.initialized
    assert cache.initialized

    # Check initialization order
    assert BaseTestPlugin.initialized_plugins == ["DatabasePlugin", "CachePlugin"]

    # Clean up everything
    await manager.cleanup()

    # Check all plugins are cleaned up
    assert not db.initialized
    assert not cache.initialized
    assert not api.initialized

    # Check cleanup order (reverse of initialization with api first)
    assert BaseTestPlugin.cleaned_up_plugins == [
        "APIPlugin",
        "CachePlugin",
        "DatabasePlugin",
    ]


@pytest.mark.asyncio
async def test_aliases_and_fallbacks(reset_plugin_system):
    """Test plugin aliases and fallbacks."""
    # Register plugins
    register_plugin("db", "postgres", DatabasePlugin)
    register_plugin("db", "mysql", DatabasePlugin)

    # Register aliases
    register_plugin_alias(
        "db", "primary", "postgres", {"host": "primary.db.example.com"}
    )
    register_plugin_alias(
        "db", "secondary", "mysql", {"host": "secondary.db.example.com"}
    )

    # Register fallbacks
    register_plugin_fallbacks("db", ["postgres", "mysql"])

    # Create instance using alias
    primary_db = await create_and_initialize_provider("db", "primary")

    # Check instance is created with the right config
    assert primary_db.initialized
    assert primary_db.host == "primary.db.example.com"

    # Create instance with fallback
    # This should fall back to postgres since the provider doesn't exist
    fallback_db = await create_and_initialize_provider("db", "nonexistent")

    # Check fallback worked
    assert fallback_db.initialized
    assert isinstance(fallback_db, DatabasePlugin)

    # Clean up
    await primary_db.cleanup()
    await fallback_db.cleanup()
