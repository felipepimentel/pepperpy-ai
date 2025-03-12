"""Schema migration and versioning system.

This module provides functionality for schema versioning, migration, and evolution.
It allows tracking schema versions, defining migrations between versions, and
applying migrations to data.
"""

import datetime
import hashlib
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pepperpy.data.errors import SchemaError, ValidationError
from pepperpy.data.schema import get_schema, register_json_schema
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class MigrationDirection(Enum):
    """Direction of schema migration."""

    FORWARD = "forward"  # Migrate from older to newer schema
    BACKWARD = "backward"  # Migrate from newer to older schema


class SchemaVersion:
    """Schema version.

    This class represents a specific version of a schema, including its
    definition and metadata.
    """

    def __init__(
        self,
        schema_name: str,
        version: str,
        schema_definition: Dict[str, Any],
        description: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        """Initialize a schema version.

        Args:
            schema_name: The name of the schema
            version: The version identifier (e.g., "1.0.0")
            schema_definition: The schema definition
            description: Optional description of this version
            created_at: Optional creation timestamp
        """
        self.schema_name = schema_name
        self.version = version
        self.schema_definition = schema_definition
        self.description = description
        self.created_at = created_at or datetime.datetime.now()
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a hash of the schema definition.

        Returns:
            A hash string representing the schema definition
        """
        schema_json = json.dumps(self.schema_definition, sort_keys=True)
        return hashlib.sha256(schema_json.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns:
            A dictionary representation of this schema version
        """
        return {
            "schema_name": self.schema_name,
            "version": self.version,
            "schema_definition": self.schema_definition,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaVersion":
        """Create a schema version from a dictionary.

        Args:
            data: The dictionary representation

        Returns:
            A SchemaVersion instance
        """
        created_at = (
            datetime.datetime.fromisoformat(data["created_at"])
            if "created_at" in data and data["created_at"]
            else None
        )
        return cls(
            schema_name=data["schema_name"],
            version=data["version"],
            schema_definition=data["schema_definition"],
            description=data.get("description"),
            created_at=created_at,
        )

    def register(self) -> None:
        """Register this schema version.

        This method registers the schema with a name that includes the version.

        Raises:
            SchemaError: If registration fails
        """
        versioned_name = f"{self.schema_name}_v{self.version}"
        register_json_schema(versioned_name, self.schema_definition)
        logger.info(
            f"Registered schema version: {versioned_name}",
            extra={"schema_name": self.schema_name, "version": self.version},
        )


class Migration(ABC):
    """Base class for schema migrations.

    This class defines the interface for schema migrations, which transform
    data from one schema version to another.
    """

    def __init__(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        description: Optional[str] = None,
    ):
        """Initialize a migration.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            description: Optional description of this migration
        """
        self.schema_name = schema_name
        self.source_version = source_version
        self.target_version = target_version
        self.description = description

    @abstractmethod
    def migrate_forward(self, data: Any) -> Any:
        """Migrate data forward (from source to target version).

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        pass

    @abstractmethod
    def migrate_backward(self, data: Any) -> Any:
        """Migrate data backward (from target to source version).

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        pass

    def migrate(self, data: Any, direction: MigrationDirection) -> Any:
        """Migrate data in the specified direction.

        Args:
            data: The data to migrate
            direction: The migration direction

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        if direction == MigrationDirection.FORWARD:
            return self.migrate_forward(data)
        else:
            return self.migrate_backward(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns:
            A dictionary representation of this migration
        """
        return {
            "schema_name": self.schema_name,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "description": self.description,
            "type": self.__class__.__name__,
        }


class FunctionMigration(Migration):
    """Migration that uses functions to transform data.

    This migration uses separate functions for forward and backward migrations.
    """

    def __init__(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        forward_func: Callable[[Any], Any],
        backward_func: Callable[[Any], Any],
        description: Optional[str] = None,
    ):
        """Initialize a function migration.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            forward_func: Function to migrate data forward
            backward_func: Function to migrate data backward
            description: Optional description of this migration
        """
        super().__init__(schema_name, source_version, target_version, description)
        self._forward_func = forward_func
        self._backward_func = backward_func

    def migrate_forward(self, data: Any) -> Any:
        """Migrate data forward using the forward function.

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        try:
            return self._forward_func(data)
        except Exception as e:
            raise ValidationError(
                message=f"Forward migration failed: {e}",
                schema_name=f"{self.schema_name}_v{self.source_version}",
                field_name=None,
                details={"error": str(e), "data": data},
            )

    def migrate_backward(self, data: Any) -> Any:
        """Migrate data backward using the backward function.

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        try:
            return self._backward_func(data)
        except Exception as e:
            raise ValidationError(
                message=f"Backward migration failed: {e}",
                schema_name=f"{self.schema_name}_v{self.target_version}",
                field_name=None,
                details={"error": str(e), "data": data},
            )


class FieldMigration(Migration):
    """Migration that transforms specific fields.

    This migration applies transformations to specific fields in the data.
    """

    def __init__(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        field_mappings: Dict[str, Union[str, Dict[str, Any]]],
        description: Optional[str] = None,
    ):
        """Initialize a field migration.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            field_mappings: Mappings between source and target fields
            description: Optional description of this migration
        """
        super().__init__(schema_name, source_version, target_version, description)
        self._field_mappings = field_mappings
        self._reverse_mappings = self._create_reverse_mappings()

    def _create_reverse_mappings(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """Create reverse mappings for backward migration.

        Returns:
            Reverse field mappings
        """
        reverse_mappings = {}
        for source, target in self._field_mappings.items():
            if isinstance(target, str):
                reverse_mappings[target] = source
            elif isinstance(target, dict) and "field" in target:
                # Handle complex mappings with transformations
                target_field = target["field"]
                reverse_mappings[target_field] = {
                    "field": source,
                    "transform": target.get("reverse_transform"),
                }
        return reverse_mappings

    def _apply_mapping(
        self, data: Dict[str, Any], mappings: Dict[str, Union[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Apply field mappings to data.

        Args:
            data: The data to transform
            mappings: The field mappings to apply

        Returns:
            Transformed data
        """
        result = {}
        # First, copy fields that aren't in the mapping
        for key, value in data.items():
            if key not in mappings:
                result[key] = value

        # Then apply mappings
        for source, target in mappings.items():
            if source not in data:
                continue

            if isinstance(target, str):
                # Simple field rename
                result[target] = data[source]
            elif isinstance(target, dict) and "field" in target:
                # Complex mapping with transformation
                target_field = target["field"]
                transform = target.get("transform")
                if transform and callable(transform):
                    result[target_field] = transform(data[source])
                else:
                    result[target_field] = data[source]

        return result

    def migrate_forward(self, data: Any) -> Any:
        """Migrate data forward by applying field mappings.

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        if not isinstance(data, dict):
            raise ValidationError(
                message="Data must be a dictionary for field migration",
                schema_name=f"{self.schema_name}_v{self.source_version}",
            )

        try:
            return self._apply_mapping(data, self._field_mappings)
        except Exception as e:
            raise ValidationError(
                message=f"Forward field migration failed: {e}",
                schema_name=f"{self.schema_name}_v{self.source_version}",
                details={"error": str(e), "data": data},
            )

    def migrate_backward(self, data: Any) -> Any:
        """Migrate data backward by applying reverse field mappings.

        Args:
            data: The data to migrate

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        if not isinstance(data, dict):
            raise ValidationError(
                message="Data must be a dictionary for field migration",
                schema_name=f"{self.schema_name}_v{self.target_version}",
            )

        try:
            return self._apply_mapping(data, self._reverse_mappings)
        except Exception as e:
            raise ValidationError(
                message=f"Backward field migration failed: {e}",
                schema_name=f"{self.schema_name}_v{self.target_version}",
                details={"error": str(e), "data": data},
            )


class MigrationPath:
    """Path of migrations between schema versions.

    This class represents a sequence of migrations that transform data
    from one schema version to another.
    """

    def __init__(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        migrations: List[Migration],
    ):
        """Initialize a migration path.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            migrations: The sequence of migrations to apply
        """
        self.schema_name = schema_name
        self.source_version = source_version
        self.target_version = target_version
        self.migrations = migrations

    def migrate(self, data: Any, direction: MigrationDirection) -> Any:
        """Migrate data along this path.

        Args:
            data: The data to migrate
            direction: The migration direction

        Returns:
            The migrated data

        Raises:
            ValidationError: If migration fails
        """
        result = data
        migrations_to_apply = (
            self.migrations
            if direction == MigrationDirection.FORWARD
            else reversed(self.migrations)
        )

        for migration in migrations_to_apply:
            result = migration.migrate(result, direction)

        return result


class SchemaVersionRegistry:
    """Registry for schema versions.

    This registry stores and retrieves schema versions.
    """

    def __init__(self):
        """Initialize a schema version registry."""
        self._versions: Dict[str, Dict[str, SchemaVersion]] = {}

    def register_version(self, version: SchemaVersion) -> None:
        """Register a schema version.

        Args:
            version: The schema version to register

        Raises:
            SchemaError: If the version is already registered
        """
        if version.schema_name not in self._versions:
            self._versions[version.schema_name] = {}

        if version.version in self._versions[version.schema_name]:
            raise SchemaError(
                f"Schema version {version.schema_name} v{version.version} is already registered"
            )

        self._versions[version.schema_name][version.version] = version
        version.register()

    def get_version(self, schema_name: str, version: str) -> SchemaVersion:
        """Get a schema version.

        Args:
            schema_name: The name of the schema
            version: The version to get

        Returns:
            The schema version

        Raises:
            SchemaError: If the version is not registered
        """
        if schema_name not in self._versions:
            raise SchemaError(f"Schema {schema_name} has no registered versions")

        if version not in self._versions[schema_name]:
            raise SchemaError(
                f"Schema version {schema_name} v{version} is not registered"
            )

        return self._versions[schema_name][version]

    def list_versions(self, schema_name: str) -> List[str]:
        """List versions of a schema.

        Args:
            schema_name: The name of the schema

        Returns:
            The versions of the schema

        Raises:
            SchemaError: If the schema has no registered versions
        """
        if schema_name not in self._versions:
            raise SchemaError(f"Schema {schema_name} has no registered versions")

        return list(self._versions[schema_name].keys())

    def get_latest_version(self, schema_name: str) -> SchemaVersion:
        """Get the latest version of a schema.

        Args:
            schema_name: The name of the schema

        Returns:
            The latest schema version

        Raises:
            SchemaError: If the schema has no registered versions
        """
        versions = self.list_versions(schema_name)
        if not versions:
            raise SchemaError(f"Schema {schema_name} has no registered versions")

        # Sort versions using semantic versioning
        latest = sorted(
            versions,
            key=lambda v: [int(x) for x in v.split(".") if x.isdigit()],
            reverse=True,
        )[0]

        return self.get_version(schema_name, latest)


class MigrationRegistry:
    """Registry for schema migrations.

    This registry stores and retrieves schema migrations.
    """

    def __init__(self):
        """Initialize a migration registry."""
        self._migrations: Dict[str, Dict[Tuple[str, str], Migration]] = {}

    def register_migration(self, migration: Migration) -> None:
        """Register a migration.

        Args:
            migration: The migration to register

        Raises:
            SchemaError: If the migration is already registered
        """
        schema_name = migration.schema_name
        if schema_name not in self._migrations:
            self._migrations[schema_name] = {}

        key = (migration.source_version, migration.target_version)
        if key in self._migrations[schema_name]:
            raise SchemaError(
                f"Migration from {schema_name} v{migration.source_version} to v{migration.target_version} is already registered"
            )

        self._migrations[schema_name][key] = migration

    def get_migration(
        self, schema_name: str, source_version: str, target_version: str
    ) -> Migration:
        """Get a migration.

        Args:
            schema_name: The name of the schema
            source_version: The source version
            target_version: The target version

        Returns:
            The migration

        Raises:
            SchemaError: If the migration is not registered
        """
        if schema_name not in self._migrations:
            raise SchemaError(f"Schema {schema_name} has no registered migrations")

        key = (source_version, target_version)
        if key not in self._migrations[schema_name]:
            raise SchemaError(
                f"Migration from {schema_name} v{source_version} to v{target_version} is not registered"
            )

        return self._migrations[schema_name][key]

    def find_migration_path(
        self, schema_name: str, source_version: str, target_version: str
    ) -> MigrationPath:
        """Find a path of migrations between two schema versions.

        Args:
            schema_name: The name of the schema
            source_version: The source version
            target_version: The target version

        Returns:
            A path of migrations

        Raises:
            SchemaError: If no path is found
        """
        if schema_name not in self._migrations:
            raise SchemaError(f"Schema {schema_name} has no registered migrations")

        if source_version == target_version:
            return MigrationPath(schema_name, source_version, target_version, [])

        # Use breadth-first search to find the shortest path
        queue = [(source_version, [])]
        visited = set()

        while queue:
            current_version, path = queue.pop(0)
            if current_version == target_version:
                return MigrationPath(schema_name, source_version, target_version, path)

            if current_version in visited:
                continue

            visited.add(current_version)

            # Find all direct migrations from the current version
            for (src, tgt), migration in self._migrations[schema_name].items():
                if src == current_version and tgt not in visited:
                    queue.append((tgt, path + [migration]))

        raise SchemaError(
            f"No migration path found from {schema_name} v{source_version} to v{target_version}"
        )


class SchemaEvolutionManager:
    """Manager for schema evolution.

    This class provides methods for managing schema versions and migrations,
    and for migrating data between schema versions.
    """

    def __init__(
        self,
        version_registry: Optional[SchemaVersionRegistry] = None,
        migration_registry: Optional[MigrationRegistry] = None,
    ):
        """Initialize a schema evolution manager.

        Args:
            version_registry: Optional schema version registry
            migration_registry: Optional migration registry
        """
        self._version_registry = version_registry or SchemaVersionRegistry()
        self._migration_registry = migration_registry or MigrationRegistry()

    @property
    def version_registry(self) -> SchemaVersionRegistry:
        """Get the schema version registry.

        Returns:
            The schema version registry
        """
        return self._version_registry

    @property
    def migration_registry(self) -> MigrationRegistry:
        """Get the migration registry.

        Returns:
            The migration registry
        """
        return self._migration_registry

    def register_schema_version(
        self,
        schema_name: str,
        version: str,
        schema_definition: Dict[str, Any],
        description: Optional[str] = None,
    ) -> SchemaVersion:
        """Register a schema version.

        Args:
            schema_name: The name of the schema
            version: The version identifier
            schema_definition: The schema definition
            description: Optional description of this version

        Returns:
            The registered schema version

        Raises:
            SchemaError: If the version is already registered
        """
        schema_version = SchemaVersion(
            schema_name=schema_name,
            version=version,
            schema_definition=schema_definition,
            description=description,
        )
        self._version_registry.register_version(schema_version)
        return schema_version

    def register_function_migration(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        forward_func: Callable[[Any], Any],
        backward_func: Callable[[Any], Any],
        description: Optional[str] = None,
    ) -> Migration:
        """Register a function migration.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            forward_func: Function to migrate data forward
            backward_func: Function to migrate data backward
            description: Optional description of this migration

        Returns:
            The registered migration

        Raises:
            SchemaError: If the migration is already registered
        """
        migration = FunctionMigration(
            schema_name=schema_name,
            source_version=source_version,
            target_version=target_version,
            forward_func=forward_func,
            backward_func=backward_func,
            description=description,
        )
        self._migration_registry.register_migration(migration)
        return migration

    def register_field_migration(
        self,
        schema_name: str,
        source_version: str,
        target_version: str,
        field_mappings: Dict[str, Union[str, Dict[str, Any]]],
        description: Optional[str] = None,
    ) -> Migration:
        """Register a field migration.

        Args:
            schema_name: The name of the schema
            source_version: The source schema version
            target_version: The target schema version
            field_mappings: Mappings between source and target fields
            description: Optional description of this migration

        Returns:
            The registered migration

        Raises:
            SchemaError: If the migration is already registered
        """
        migration = FieldMigration(
            schema_name=schema_name,
            source_version=source_version,
            target_version=target_version,
            field_mappings=field_mappings,
            description=description,
        )
        self._migration_registry.register_migration(migration)
        return migration

    def migrate_data(
        self,
        schema_name: str,
        data: Any,
        source_version: str,
        target_version: str,
    ) -> Any:
        """Migrate data from one schema version to another.

        Args:
            schema_name: The name of the schema
            data: The data to migrate
            source_version: The source schema version
            target_version: The target schema version

        Returns:
            The migrated data

        Raises:
            SchemaError: If no migration path is found
            ValidationError: If migration fails
        """
        if source_version == target_version:
            return data

        # Find migration path
        path = self._migration_registry.find_migration_path(
            schema_name, source_version, target_version
        )

        # Determine migration direction
        direction = MigrationDirection.FORWARD

        # Migrate data
        return path.migrate(data, direction)

    def validate_data(
        self, schema_name: str, data: Any, version: Optional[str] = None
    ) -> Any:
        """Validate data against a schema version.

        Args:
            schema_name: The name of the schema
            data: The data to validate
            version: The schema version, or None to use the latest version

        Returns:
            The validated data

        Raises:
            SchemaError: If the schema version is not registered
            ValidationError: If validation fails
        """
        # Get the schema version
        if version is None:
            schema_version = self._version_registry.get_latest_version(schema_name)
        else:
            schema_version = self._version_registry.get_version(schema_name, version)

        # Get the schema
        versioned_name = f"{schema_name}_v{schema_version.version}"
        schema = get_schema(versioned_name)

        # Validate data
        return schema.validate(data)


# Global schema evolution manager
_manager: Optional[SchemaEvolutionManager] = None


def get_manager() -> SchemaEvolutionManager:
    """Get the global schema evolution manager.

    Returns:
        The global schema evolution manager
    """
    global _manager
    if _manager is None:
        _manager = SchemaEvolutionManager()
    return _manager


def set_manager(manager: SchemaEvolutionManager) -> None:
    """Set the global schema evolution manager.

    Args:
        manager: The schema evolution manager to set
    """
    global _manager
    _manager = manager


def register_schema_version(
    schema_name: str,
    version: str,
    schema_definition: Dict[str, Any],
    description: Optional[str] = None,
) -> SchemaVersion:
    """Register a schema version.

    Args:
        schema_name: The name of the schema
        version: The version identifier
        schema_definition: The schema definition
        description: Optional description of this version

    Returns:
        The registered schema version

    Raises:
        SchemaError: If the version is already registered
    """
    return get_manager().register_schema_version(
        schema_name, version, schema_definition, description
    )


def register_function_migration(
    schema_name: str,
    source_version: str,
    target_version: str,
    forward_func: Callable[[Any], Any],
    backward_func: Callable[[Any], Any],
    description: Optional[str] = None,
) -> Migration:
    """Register a function migration.

    Args:
        schema_name: The name of the schema
        source_version: The source schema version
        target_version: The target schema version
        forward_func: Function to migrate data forward
        backward_func: Function to migrate data backward
        description: Optional description of this migration

    Returns:
        The registered migration

    Raises:
        SchemaError: If the migration is already registered
    """
    return get_manager().register_function_migration(
        schema_name,
        source_version,
        target_version,
        forward_func,
        backward_func,
        description,
    )


def register_field_migration(
    schema_name: str,
    source_version: str,
    target_version: str,
    field_mappings: Dict[str, Union[str, Dict[str, Any]]],
    description: Optional[str] = None,
) -> Migration:
    """Register a field migration.

    Args:
        schema_name: The name of the schema
        source_version: The source schema version
        target_version: The target schema version
        field_mappings: Mappings between source and target fields
        description: Optional description of this migration

    Returns:
        The registered migration

    Raises:
        SchemaError: If the migration is already registered
    """
    return get_manager().register_field_migration(
        schema_name, source_version, target_version, field_mappings, description
    )


def migrate_data(
    schema_name: str,
    data: Any,
    source_version: str,
    target_version: str,
) -> Any:
    """Migrate data from one schema version to another.

    Args:
        schema_name: The name of the schema
        data: The data to migrate
        source_version: The source schema version
        target_version: The target schema version

    Returns:
        The migrated data

    Raises:
        SchemaError: If no migration path is found
        ValidationError: If migration fails
    """
    return get_manager().migrate_data(schema_name, data, source_version, target_version)


def validate_data(schema_name: str, data: Any, version: Optional[str] = None) -> Any:
    """Validate data against a schema version.

    Args:
        schema_name: The name of the schema
        data: The data to validate
        version: The schema version, or None to use the latest version

    Returns:
        The validated data

    Raises:
        SchemaError: If the schema version is not registered
        ValidationError: If validation fails
    """
    return get_manager().validate_data(schema_name, data, version)
