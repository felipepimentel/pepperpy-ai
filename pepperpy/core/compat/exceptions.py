"""Custom exceptions for the compatibility system."""

from typing import Optional


class MigrationError(Exception):
    """Base class for migration-related errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize the error.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.details = details or {}


class NoMigrationPathError(MigrationError):
    """Raised when no migration path exists between versions."""

    def __init__(
        self,
        source_version: str,
        target_version: str,
        data_type: str,
        details: Optional[dict] = None,
    ):
        """Initialize the error.
        
        Args:
            source_version: Source version string
            target_version: Target version string
            data_type: Type of data being migrated
            details: Optional dictionary with additional error details
        """
        message = (
            f"No migration path found from version {source_version} to "
            f"{target_version} for data type {data_type}"
        )
        super().__init__(message, details)
        self.source_version = source_version
        self.target_version = target_version
        self.data_type = data_type


class InvalidVersionError(MigrationError):
    """Raised when a version string is invalid."""

    def __init__(self, version: str, details: Optional[dict] = None):
        """Initialize the error.
        
        Args:
            version: Invalid version string
            details: Optional dictionary with additional error details
        """
        message = f"Invalid version string: {version}"
        super().__init__(message, details)
        self.version = version


class MigrationRegistrationError(MigrationError):
    """Raised when there's an error registering a migration."""

    def __init__(
        self,
        data_type: str,
        source_version: str,
        target_version: str,
        details: Optional[dict] = None,
    ):
        """Initialize the error.
        
        Args:
            data_type: Type of data for the migration
            source_version: Source version string
            target_version: Target version string
            details: Optional dictionary with additional error details
        """
        message = (
            f"Error registering migration for {data_type} from "
            f"{source_version} to {target_version}"
        )
        super().__init__(message, details)
        self.data_type = data_type
        self.source_version = source_version
        self.target_version = target_version 