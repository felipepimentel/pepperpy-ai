"""Version migration manager.

This module provides functionality for managing version migrations:

- MigrationManager: Core class for managing version migrations
- Migration path planning and execution
- Version upgrade and downgrade operations
- Migration validation and verification
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..errors import VersionCompatibilityError
from ..types import Version


class MigrationManager:
    """Manager for version migrations."""

    def __init__(self) -> None:
        """Initialize migration manager."""
        self._migrations: Dict[Tuple[Version, Version], Callable[[], None]] = {}
        self._dependencies: Dict[
            Tuple[Version, Version], Set[Tuple[Version, Version]]
        ] = {}

    def register_migration(
        self,
        from_version: Version,
        to_version: Version,
        migration_func: Callable[[], None],
        dependencies: Optional[List[Tuple[Version, Version]]] = None,
    ) -> None:
        """Register a migration between versions.

        Args:
            from_version: Source version
            to_version: Target version
            migration_func: Migration function
            dependencies: Optional list of migration dependencies
        """
        migration_key = (from_version, to_version)
        self._migrations[migration_key] = migration_func

        if dependencies:
            self._dependencies[migration_key] = set(dependencies)
        else:
            self._dependencies[migration_key] = set()

    def get_migration(
        self, from_version: Version, to_version: Version
    ) -> Optional[Callable[[], None]]:
        """Get migration function between versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            Migration function if registered, None otherwise
        """
        return self._migrations.get((from_version, to_version))

    def get_dependencies(
        self, from_version: Version, to_version: Version
    ) -> Set[Tuple[Version, Version]]:
        """Get dependencies for a migration.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            Set of migration dependencies
        """
        return self._dependencies.get((from_version, to_version), set())

    def plan_migration(
        self, from_version: Version, to_version: Version
    ) -> List[Tuple[Version, Version]]:
        """Plan migration path between versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            List of migration steps

        Raises:
            VersionCompatibilityError: If no migration path is found
        """
        # Direct migration
        if (from_version, to_version) in self._migrations:
            return [(from_version, to_version)]

        # TODO: Implement path finding algorithm
        # For now, just return empty list if no direct migration
        raise VersionCompatibilityError(
            from_version,
            to_version,
            "No migration path found",
        )

    def execute_migration(self, from_version: Version, to_version: Version) -> None:
        """Execute migration between versions.

        Args:
            from_version: Source version
            to_version: Target version

        Raises:
            VersionCompatibilityError: If migration fails
        """
        try:
            migration_path = self.plan_migration(from_version, to_version)
            for step_from, step_to in migration_path:
                migration_func = self.get_migration(step_from, step_to)
                if migration_func:
                    migration_func()
                else:
                    raise VersionCompatibilityError(
                        step_from,
                        step_to,
                        "Missing migration function",
                    )
        except Exception as e:
            raise VersionCompatibilityError(
                from_version,
                to_version,
                f"Migration failed: {str(e)}",
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert migration manager state to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "migrations": [
                {
                    "from": str(k[0]),
                    "to": str(k[1]),
                    "dependencies": [
                        {"from": str(d[0]), "to": str(d[1])}
                        for d in self._dependencies.get(k, set())
                    ],
                }
                for k in self._migrations
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationManager":
        """Create migration manager from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            MigrationManager instance
        """
        manager = cls()
        # Note: This only restores the structure, not the actual migration functions
        for migration in data.get("migrations", []):
            from_version = Version.parse(migration["from"])
            to_version = Version.parse(migration["to"])
            dependencies = [
                (Version.parse(d["from"]), Version.parse(d["to"]))
                for d in migration.get("dependencies", [])
            ]
            # Register a placeholder function
            manager.register_migration(
                from_version, to_version, lambda: None, dependencies
            )
        return manager
