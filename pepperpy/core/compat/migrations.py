"""Base classes and types for data migrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, List, Dict, Any, Optional

from .models import VersionInfo

T = TypeVar("T")


@dataclass
class MigrationPath:
    """Represents a path of migrations between versions."""

    data_type: str
    source_version: VersionInfo
    target_version: VersionInfo
    migrations: List["Migration[Any]"]

    def __post_init__(self):
        """Validate the migration path after initialization."""
        if not self.migrations:
            return

        # Verify path continuity
        for i in range(len(self.migrations) - 1):
            current = self.migrations[i]
            next_migration = self.migrations[i + 1]
            if current.target_version != next_migration.source_version:
                raise ValueError(
                    f"Invalid migration path: gap between "
                    f"{current.target_version} and "
                    f"{next_migration.source_version}"
                )

        # Verify path endpoints
        if str(self.source_version) != str(self.migrations[0].source_version):
            raise ValueError(
                f"Path starts at {self.migrations[0].source_version}, "
                f"expected {self.source_version}"
            )
        if str(self.target_version) != str(self.migrations[-1].target_version):
            raise ValueError(
                f"Path ends at {self.migrations[-1].target_version}, "
                f"expected {self.target_version}"
            )


class Migration(Generic[T], ABC):
    """Base class for data migrations."""

    def __init__(self, data_type: str):
        """Initialize the migration.
        
        Args:
            data_type: Type of data this migration handles
        """
        self.data_type = data_type
        self._source_version: Optional[VersionInfo] = None
        self._target_version: Optional[VersionInfo] = None

    @property
    @abstractmethod
    def source_version(self) -> str:
        """Get the source version string."""
        pass

    @property
    def source_version_info(self) -> VersionInfo:
        """Get the source version info.
        
        Returns:
            VersionInfo for the source version
        """
        if self._source_version is None:
            self._source_version = VersionInfo.from_string(self.source_version)
        return self._source_version

    @property
    @abstractmethod
    def target_version(self) -> str:
        """Get the target version string."""
        pass

    @property
    def target_version_info(self) -> VersionInfo:
        """Get the target version info.
        
        Returns:
            VersionInfo for the target version
        """
        if self._target_version is None:
            self._target_version = VersionInfo.from_string(self.target_version)
        return self._target_version

    @abstractmethod
    async def migrate_forward(self, data: T) -> T:
        """Migrate data forward from source to target version.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        pass

    @abstractmethod
    async def migrate_backward(self, data: T) -> T:
        """Migrate data backward from target to source version.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        pass

    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String describing the migration
        """
        return (
            f"{self.__class__.__name__}({self.data_type}: "
            f"{self.source_version} -> {self.target_version})"
        ) 