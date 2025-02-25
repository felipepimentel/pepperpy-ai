"""Tests for the compatibility system."""

import pytest

from pepperpy.core.compat import (
    InvalidVersionError,
    MigrationManager,
    NoMigrationPathError,
    VersionInfo,
)
from pepperpy.core.compat.memory import (
    MemoryEntryMigration_1_0_0_to_2_0_0,
    MemoryEntryMigration_2_0_0_to_3_0_0,
)


@pytest.fixture
def migration_manager():
    """Create a fresh migration manager for testing."""
    manager = MigrationManager()
    manager._migrations.clear()  # Clear any existing migrations
    return manager


@pytest.fixture
def memory_migrations(migration_manager):
    """Register memory migrations for testing."""
    migrations = [
        MemoryEntryMigration_1_0_0_to_2_0_0(),
        MemoryEntryMigration_2_0_0_to_3_0_0(),
    ]
    for migration in migrations:
        migration_manager.register_migration(migration)
    return migrations


class TestVersionInfo:
    """Tests for VersionInfo."""

    def test_version_parsing(self):
        """Test parsing version strings."""
        version = VersionInfo.from_string("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
        assert version.build is None

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = VersionInfo.from_string("1.0.0")
        v2 = VersionInfo.from_string("2.0.0")
        v3 = VersionInfo.from_string("2.1.0")

        assert v1 < v2
        assert v2 < v3
        assert not v2 < v1

    def test_invalid_version(self):
        """Test invalid version strings."""
        with pytest.raises(InvalidVersionError):
            VersionInfo.from_string("invalid")

        with pytest.raises(InvalidVersionError):
            VersionInfo.from_string("1.0")


class TestMigrationManager:
    """Tests for MigrationManager."""

    async def test_memory_migration_1_to_2(self, migration_manager, memory_migrations):
        """Test migrating memory entry from v1 to v2."""
        original_data = {
            "key": "test",
            "value": {"data": "test"},
            "type": "test_type",
            "scope": "test_scope",
            "timestamp": "2024-01-01T00:00:00",
        }

        migrated = await migration_manager.migrate(
            "memory_entry",
            original_data,
            "1.0.0",
            "2.0.0",
        )

        assert migrated["key"] == original_data["key"]
        assert migrated["value"] == original_data["value"]
        assert migrated["metadata"]["type"] == original_data["type"]
        assert migrated["metadata"]["scope"] == original_data["scope"]
        assert migrated["metadata"]["created_at"] == original_data["timestamp"]
        assert migrated["metadata"]["version"] == "2.0.0"

    async def test_memory_migration_2_to_3(self, migration_manager, memory_migrations):
        """Test migrating memory entry from v2 to v3."""
        original_data = {
            "key": "test",
            "value": {"data": "test"},
            "metadata": {
                "type": "test_type",
                "scope": "test_scope",
                "created_at": "2024-01-01T00:00:00",
                "version": "2.0.0",
            },
        }

        migrated = await migration_manager.migrate(
            "memory_entry",
            original_data,
            "2.0.0",
            "3.0.0",
        )

        assert migrated["key"] == original_data["key"]
        assert migrated["value"] == original_data["value"]
        assert migrated["metadata"]["type"] == original_data["metadata"]["type"]
        assert migrated["metadata"]["scope"] == original_data["metadata"]["scope"]
        assert (
            migrated["metadata"]["created_at"]
            == original_data["metadata"]["created_at"]
        )
        assert migrated["metadata"]["version"] == "3.0.0"
        assert "updated_at" in migrated["metadata"]
        assert "tags" in migrated["metadata"]
        assert "checksum" in migrated["metadata"]

    async def test_memory_migration_1_to_3(self, migration_manager, memory_migrations):
        """Test migrating memory entry from v1 to v3 (multi-step)."""
        original_data = {
            "key": "test",
            "value": {"data": "test"},
            "type": "test_type",
            "scope": "test_scope",
            "timestamp": "2024-01-01T00:00:00",
        }

        migrated = await migration_manager.migrate(
            "memory_entry",
            original_data,
            "1.0.0",
            "3.0.0",
        )

        assert migrated["key"] == original_data["key"]
        assert migrated["value"] == original_data["value"]
        assert migrated["metadata"]["type"] == original_data["type"]
        assert migrated["metadata"]["scope"] == original_data["scope"]
        assert migrated["metadata"]["created_at"] == original_data["timestamp"]
        assert migrated["metadata"]["version"] == "3.0.0"
        assert "updated_at" in migrated["metadata"]
        assert "tags" in migrated["metadata"]
        assert "checksum" in migrated["metadata"]

    async def test_no_migration_path(self, migration_manager):
        """Test error when no migration path exists."""
        with pytest.raises(NoMigrationPathError):
            await migration_manager.migrate(
                "unknown_type",
                {"data": "test"},
                "1.0.0",
                "2.0.0",
            )

    async def test_backward_migration(self, migration_manager, memory_migrations):
        """Test migrating backward from v3 to v1."""
        original_data = {
            "key": "test",
            "value": {"data": "test"},
            "metadata": {
                "type": "test_type",
                "scope": "test_scope",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
                "tags": ["test"],
                "checksum": "abc123",
                "version": "3.0.0",
            },
        }

        migrated = await migration_manager.migrate(
            "memory_entry",
            original_data,
            "3.0.0",
            "1.0.0",
        )
        assert migrated["key"] == original_data["key"]
        assert migrated["value"] == original_data["value"]
        assert migrated["type"] == original_data["metadata"]["type"]
        assert migrated["scope"] == original_data["metadata"]["scope"]
        assert migrated["timestamp"] == original_data["metadata"]["created_at"]
