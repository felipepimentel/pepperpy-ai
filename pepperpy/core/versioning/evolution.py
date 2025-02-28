"""Schema evolution management for versioned data.

This module provides tools for managing schema evolution across versions:

- SchemaEvolution: Core class for managing schema changes
- SchemaVersion: Representation of a schema at a specific version
- SchemaMigrator: Interface for migrating between schema versions
- SchemaValidator: Interface for validating data against a schema
- SchemaRegistry: Registry of available schemas and migrations

The schema evolution system enables safe data migration between different
versions of the framework, ensuring backward and forward compatibility
for persistent data structures.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Union

from .base import Version, VersionedObject
from .errors import MigrationError
from .types import VersionString

T = TypeVar("T")
SchemaType = Dict[str, Any]


class SchemaVersion(VersionedObject):
    """Representation of a schema at a specific version."""

    def __init__(self, version: Version, schema: SchemaType):
        self._version = version
        self._schema = schema

    @property
    def version(self) -> Version:
        """Get schema version."""
        return self._version

    @property
    def schema(self) -> SchemaType:
        """Get schema definition."""
        return self._schema

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Check if schema is compatible with other schema."""
        return self.version.is_compatible_with(other.version)

    def validate(self, data: Any) -> bool:
        """Validate data against schema.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        # Basic implementation - should be overridden in subclasses
        return True


class SchemaMigrator(ABC):
    """Interface for migrating between schema versions."""

    @abstractmethod
    def can_migrate(self, source: SchemaVersion, target: SchemaVersion) -> bool:
        """Check if migration is possible.

        Args:
            source: Source schema version
            target: Target schema version

        Returns:
            True if migration is possible
        """
        pass

    @abstractmethod
    def migrate(self, data: Any, source: SchemaVersion, target: SchemaVersion) -> Any:
        """Migrate data from source to target schema.

        Args:
            data: Data to migrate
            source: Source schema version
            target: Target schema version

        Returns:
            Migrated data

        Raises:
            MigrationError: If migration fails
        """
        pass


class SchemaValidator(ABC):
    """Interface for validating data against a schema."""

    @abstractmethod
    def validate(self, data: Any, schema: SchemaVersion) -> bool:
        """Validate data against schema.

        Args:
            data: Data to validate
            schema: Schema to validate against

        Returns:
            True if data is valid
        """
        pass

    @abstractmethod
    def get_validation_errors(self, data: Any, schema: SchemaVersion) -> List[str]:
        """Get validation errors.

        Args:
            data: Data to validate
            schema: Schema to validate against

        Returns:
            List of validation error messages
        """
        pass


class SchemaRegistry:
    """Registry of available schemas and migrations."""

    def __init__(self):
        self._schemas: Dict[VersionString, SchemaVersion] = {}
        self._migrators: List[SchemaMigrator] = []

    def register_schema(self, schema: SchemaVersion) -> None:
        """Register a schema.

        Args:
            schema: Schema to register
        """
        self._schemas[str(schema.version)] = schema

    def register_migrator(self, migrator: SchemaMigrator) -> None:
        """Register a migrator.

        Args:
            migrator: Migrator to register
        """
        self._migrators.append(migrator)

    def get_schema(self, version: Union[Version, str]) -> Optional[SchemaVersion]:
        """Get schema by version.

        Args:
            version: Schema version

        Returns:
            Schema or None if not found
        """
        version_str = str(version)
        return self._schemas.get(version_str)

    def find_migrator(
        self, source: SchemaVersion, target: SchemaVersion
    ) -> Optional[SchemaMigrator]:
        """Find migrator for source and target schemas.

        Args:
            source: Source schema
            target: Target schema

        Returns:
            Migrator or None if not found
        """
        for migrator in self._migrators:
            if migrator.can_migrate(source, target):
                return migrator
        return None


class SchemaEvolution:
    """Core class for managing schema changes."""

    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self._registry = registry or SchemaRegistry()
        self._validator: Optional[SchemaValidator] = None

    @property
    def registry(self) -> SchemaRegistry:
        """Get schema registry."""
        return self._registry

    def set_validator(self, validator: SchemaValidator) -> None:
        """Set schema validator.

        Args:
            validator: Validator to use
        """
        self._validator = validator

    def migrate(
        self,
        data: Any,
        source_version: Union[Version, str],
        target_version: Union[Version, str],
    ) -> Any:
        """Migrate data from source to target version.

        Args:
            data: Data to migrate
            source_version: Source version
            target_version: Target version

        Returns:
            Migrated data

        Raises:
            MigrationError: If migration fails
        """
        source_schema = self._registry.get_schema(source_version)
        target_schema = self._registry.get_schema(target_version)

        if not source_schema:
            raise MigrationError(
                source_version,
                target_version,
                f"Source schema not found: {source_version}",
            )

        if not target_schema:
            raise MigrationError(
                source_version,
                target_version,
                f"Target schema not found: {target_version}",
            )

        migrator = self._registry.find_migrator(source_schema, target_schema)
        if not migrator:
            raise MigrationError(
                source_version,
                target_version,
                "No migrator found for this version pair",
            )

        # Validate source data if validator is available
        if self._validator and not self._validator.validate(data, source_schema):
            errors = self._validator.get_validation_errors(data, source_schema)
            raise MigrationError(
                source_version,
                target_version,
                f"Source data validation failed: {errors}",
            )

        # Perform migration
        migrated_data = migrator.migrate(data, source_schema, target_schema)

        # Validate migrated data if validator is available
        if self._validator and not self._validator.validate(
            migrated_data, target_schema
        ):
            errors = self._validator.get_validation_errors(migrated_data, target_schema)
            raise MigrationError(
                source_version,
                target_version,
                f"Migrated data validation failed: {errors}",
            )

        return migrated_data
