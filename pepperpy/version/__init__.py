"""
Version management system.

This module provides a comprehensive version management system that includes:
- Semantic versioning support
- Version compatibility checking
- Version migration management
- Version dependency tracking
- Version history tracking
"""

from .base import VersionManager
from .compatibility.checker import CompatibilityChecker
from .compatibility.matrix import CompatibilityMatrix
from .errors import (
    VersionCompatibilityError,
    VersionDependencyError,
    VersionError,
    VersionMigrationError,
    VersionParseError,
    VersionTrackingError,
    VersionValidationError,
)
from .migration.manager import MigrationManager
from .migration.steps import (
    MigrationContext,
    MigrationStep,
    create_data_migration_step,
    create_step,
    create_validation_step,
)
from .semver.parser import SemVerParser
from .semver.validator import SemVerValidator
from .tracking.dependencies import DependencyTracker
from .tracking.history import VersionHistory, VersionHistoryEntry
from .types import (
    Version,
    VersionChange,
    VersionChangeType,
    VersionComponent,
    VersionDependency,
    VersionType,
)

__all__ = [
    # Types
    "Version",
    "VersionType",
    "VersionComponent",
    "VersionChange",
    "VersionChangeType",
    "VersionDependency",
    # Core
    "VersionManager",
    # Errors
    "VersionError",
    "VersionParseError",
    "VersionCompatibilityError",
    "VersionMigrationError",
    "VersionValidationError",
    "VersionDependencyError",
    "VersionTrackingError",
    # Semantic Versioning
    "SemVerParser",
    "SemVerValidator",
    # Compatibility
    "CompatibilityChecker",
    "CompatibilityMatrix",
    # Migration
    "MigrationManager",
    "MigrationStep",
    "MigrationContext",
    "create_step",
    "create_data_migration_step",
    "create_validation_step",
    # Tracking
    "DependencyTracker",
    "VersionHistory",
    "VersionHistoryEntry",
]
