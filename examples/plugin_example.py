"""Example usage of the PepperPy plugin system.

This example demonstrates the key features of the plugin system:
1. Plugin registration and discovery
2. Plugin aliases and fallbacks
3. Plugin dependencies
4. Plugin lifecycle management
5. Resource management
"""

import asyncio
from typing import Any, Dict, Optional

from pepperpy.plugins import (
    PepperpyPlugin,
    ResourceMixin,
    auto_context,
    create_provider_instance,
    register_plugin,
    register_plugin_alias,
    register_plugin_fallbacks,
)
from pepperpy.plugins.manager import get_plugin_manager


# Example plugin implementations
class DatabasePlugin(PepperpyPlugin, ResourceMixin):
    """Example database plugin for demonstration."""

    # Configuration
    host: str = "localhost"
    port: int = 5432
    username: str = "user"
    password: str = "password"
    database: str = "example"

    def __init__(self, **kwargs):
        """Initialize the plugin."""
        super().__init__(**kwargs)
        self.connection = None

    async def initialize(self):
        """Initialize the database connection."""
        if self.initialized:
            return

        print(f"[Database] Connecting to {self.host}:{self.port}/{self.database}")
        # In a real plugin, this would create a real connection
        self.connection = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "database": self.database,
            "connected": True,
        }

        self.initialized = True
        print(f"[Database] Connected to {self.host}")

    async def query(self, sql: str) -> Dict[str, Any]:
        """Execute a SQL query."""
        if not self.initialized:
            await self.initialize()

        print(f"[Database] Executing query: {sql}")
        # Simulate query execution
        return {"results": ["row1", "row2"], "query": sql}

    async def cleanup(self):
        """Close the database connection."""
        if not self.initialized:
            return

        print(f"[Database] Disconnecting from {self.host}")
        if self.connection:
            self.connection["connected"] = False
            self.connection = None

        self.initialized = False


class CachePlugin(PepperpyPlugin, ResourceMixin):
    """Example cache plugin for demonstration."""

    # Configuration
    host: str = "localhost"
    port: int = 6379
    ttl: int = 3600

    def __init__(self, **kwargs):
        """Initialize the plugin."""
        super().__init__(**kwargs)
        self.client = None
        self._cache = {}  # Simple in-memory cache for demo

    async def initialize(self):
        """Initialize the cache connection."""
        if self.initialized:
            return

        print(f"[Cache] Connecting to {self.host}:{self.port}")
        # In a real plugin, this would create a real connection
        self.client = {
            "host": self.host,
            "port": self.port,
            "connected": True,
        }

        self.initialized = True
        print(f"[Cache] Connected to {self.host}")

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if not self.initialized:
            await self.initialize()

        print(f"[Cache] Getting key: {key}")
        return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        if not self.initialized:
            await self.initialize()

        print(f"[Cache] Setting key: {key}")
        self._cache[key] = value

    async def cleanup(self):
        """Close the cache connection."""
        if not self.initialized:
            return

        print(f"[Cache] Disconnecting from {self.host}")
        if self.client:
            self.client["connected"] = False
            self.client = None

        self.initialized = False


class APIPlugin(PepperpyPlugin):
    """Example API plugin that uses database and cache."""

    # Configuration
    url: str = "https://api.example.com"
    api_key: Optional[str] = None
    timeout: int = 30

    def __init__(self, **kwargs):
        """Initialize the plugin."""
        super().__init__(**kwargs)
        self.db = None
        self.cache = None

    async def initialize(self):
        """Initialize the API client and dependencies."""
        if self.initialized:
            return

        print(f"[API] Initializing API client for {self.url}")

        # In a real implementation, dependencies would be injected by the manager
        # Here we're manually loading them for demonstration
        manager = get_plugin_manager()

        # Get database instance
        self.db = manager.get_instance("db", "postgres")
        if not self.db or not self.db.initialized:
            print("[API] Database dependency not initialized")
            return

        # Get cache instance
        self.cache = manager.get_instance("cache", "redis")
        if not self.cache or not self.cache.initialized:
            print("[API] Cache dependency not initialized")
            return

        self.initialized = True
        print("[API] Initialized with dependencies")

    async def call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API call, using cache and database."""
        if not self.initialized:
            await self.initialize()

        # Type checking guard to prevent linter errors
        if not self.cache or not self.db:
            return {"error": "Dependencies not initialized"}

        # Try to get from cache first
        cache_key = f"api:{endpoint}:{data!s}"
        cached = await self.cache.get(cache_key)
        if cached:
            print(f"[API] Cache hit for {endpoint}")
            return cached

        # Query the database
        query_result = await self.db.query(
            f"SELECT * FROM data WHERE endpoint='{endpoint}'"
        )

        # Simulate API call
        print(f"[API] Calling {self.url}/{endpoint}")
        result = {
            "endpoint": endpoint,
            "data": data,
            "database_info": query_result,
            "result": "API response",
        }

        # Cache the result
        await self.cache.set(cache_key, result)

        return result

    async def cleanup(self):
        """Clean up resources."""
        if not self.initialized:
            return

        print("[API] Cleaning up")
        self.initialized = False


async def register_example_plugins():
    """Register example plugins."""
    # Register plugin classes
    register_plugin("db", "postgres", DatabasePlugin)
    register_plugin("db", "mysql", DatabasePlugin)
    register_plugin("cache", "redis", CachePlugin)
    register_plugin("cache", "memcached", CachePlugin)
    register_plugin("api", "rest", APIPlugin)

    # Register aliases
    register_plugin_alias(
        "db", "primary", "postgres", {"host": "primary.db.example.com"}
    )
    register_plugin_alias("cache", "fast", "redis", {"port": 6380})

    # Register fallbacks
    register_plugin_fallbacks("db", ["postgres", "mysql"])
    register_plugin_fallbacks("cache", ["redis", "memcached"])


async def example_basic_usage():
    """Demonstrate basic plugin usage."""
    print("\n=== Basic Plugin Usage ===\n")

    # Create a database plugin
    db = create_provider_instance(
        "db", "postgres", host="db.example.com", username="demo"
    )

    # Type check to prevent linter errors
    if not isinstance(db, DatabasePlugin):
        return

    # Initialize it
    await db.initialize()

    # Use it
    result = await db.query("SELECT * FROM users")
    print(f"Query result: {result}")

    # Clean it up
    await db.cleanup()


async def example_context_manager():
    """Demonstrate context manager usage."""
    print("\n=== Context Manager Usage ===\n")

    # Create a cache plugin
    cache = create_provider_instance("cache", "redis", host="cache.example.com")

    # Type check to prevent linter errors
    if not isinstance(cache, CachePlugin):
        return

    # Use context manager for automatic cleanup
    async with auto_context(cache):
        await cache.set("example_key", "example_value")
        value = await cache.get("example_key")
        print(f"Retrieved value: {value}")


async def example_aliases_and_fallbacks():
    """Demonstrate aliases and fallbacks."""
    print("\n=== Aliases and Fallbacks ===\n")

    # Create instance using an alias
    db = create_provider_instance("db", "primary")

    # Type check to prevent linter errors
    if not isinstance(db, DatabasePlugin):
        return

    await db.initialize()
    print(f"Created database instance with host: {db.host}")
    await db.cleanup()

    # Create instance with fallback
    # This will fall back to postgres since "nonexistent" doesn't exist
    db = create_provider_instance("db", "nonexistent")
    await db.initialize()
    print(f"Created fallback database instance: {db.__class__.__name__}")
    await db.cleanup()


async def example_dependencies():
    """Demonstrate plugin dependencies."""
    print("\n=== Plugin Dependencies ===\n")

    # Get plugin manager
    manager = get_plugin_manager()

    # Register dependencies metadata
    manager.register_plugin_metadata(
        "api",
        "rest",
        {
            "dependencies": [
                {"type": "db", "provider": "postgres"},
                {"type": "cache", "provider": "redis"},
            ]
        },
    )

    # First create and initialize the dependencies
    db = manager.create_instance("db", "postgres")
    await db.initialize()

    cache = manager.create_instance("cache", "redis")
    await cache.initialize()

    # Now create and initialize the API plugin
    api = manager.create_instance("api", "rest")
    await api.initialize()

    # Type check and make API call
    if isinstance(api, APIPlugin):
        result = await api.call("users", {"id": 123})
        print(f"API call result: {result}")

    # Clean up in reverse order
    await api.cleanup()
    await cache.cleanup()
    await db.cleanup()


async def main():
    """Run the example."""
    print("=== PepperPy Plugin System Example ===")

    # Register example plugins
    await register_example_plugins()

    # Run examples
    await example_basic_usage()
    await example_context_manager()
    await example_aliases_and_fallbacks()
    await example_dependencies()

    print("\nExample completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
