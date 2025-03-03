"""Version management and compatibility system

This module provides comprehensive versioning capabilities for the framework:

- Semantic versioning implementation (SemVer)
- Version compatibility checking
- Migration paths between versions
- Version tracking for components and data
- Schema evolution management
- Backward compatibility utilities

The versioning system ensures reliable upgrades, consistent data structures,
and proper handling of breaking changes across framework versions.
"""

from .compatibility import CompatibilityChecker, VersionRange
from .evolution import SchemaEvolution
from .migration import MigrationManager, MigrationPath
from .semver import SemVer, compare_versions, parse_version
from .tracking import VersionHistory, VersionTracker

__all__ = [
    "CompatibilityChecker",
    "MigrationManager",
    "MigrationPath",
    "SchemaEvolution",
    "SemVer",
    "VersionHistory",
    "VersionRange",
    "VersionTracker",
    "compare_versions",
    "parse_version",
]
