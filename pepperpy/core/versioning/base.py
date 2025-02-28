"""Base interfaces for the versioning system.

This module defines the core interfaces and base classes for the versioning system:

- Version: Base class for version representations
- VersionedObject: Interface for objects with version information
- VersionProvider: Interface for components that provide version information
- VersionResolver: Interface for resolving version dependencies
- VersionConstraint: Interface for version constraints and requirements

These interfaces form the foundation of the versioning system, enabling
consistent version handling across the framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Version(ABC):
    """Base class for version representations."""

    @abstractmethod
    def __str__(self) -> str:
        """Convert version to string representation."""
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """Check if versions are equal."""
        pass

    @abstractmethod
    def __lt__(self, other: Any) -> bool:
        """Check if version is less than other."""
        pass

    @abstractmethod
    def __gt__(self, other: Any) -> bool:
        """Check if version is greater than other."""
        pass

    @abstractmethod
    def is_compatible_with(self, other: "Version") -> bool:
        """Check if version is compatible with other version."""
        pass


class VersionedObject(ABC):
    """Interface for objects with version information."""

    @property
    @abstractmethod
    def version(self) -> Version:
        """Get object version."""
        pass

    @abstractmethod
    def is_compatible_with(self, other: "VersionedObject") -> bool:
        """Check if object is compatible with other object."""
        pass


class VersionProvider(ABC):
    """Interface for components that provide version information."""

    @abstractmethod
    def get_version(self) -> Version:
        """Get component version."""
        pass

    @abstractmethod
    def get_supported_versions(self) -> List[Version]:
        """Get list of supported versions."""
        pass


class VersionResolver(ABC):
    """Interface for resolving version dependencies."""

    @abstractmethod
    def resolve(self, constraints: List["VersionConstraint"]) -> Optional[Version]:
        """Resolve version constraints to a specific version.

        Args:
            constraints: List of version constraints

        Returns:
            Resolved version or None if no resolution is possible
        """
        pass


class VersionConstraint(ABC):
    """Interface for version constraints and requirements."""

    @abstractmethod
    def is_satisfied_by(self, version: Version) -> bool:
        """Check if constraint is satisfied by version.

        Args:
            version: Version to check

        Returns:
            True if constraint is satisfied
        """
        pass

    @abstractmethod
    def to_string(self) -> str:
        """Convert constraint to string representation."""
        pass
