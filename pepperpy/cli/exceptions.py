"""Exceptions for the Pepperpy CLI.

This module defines CLI-specific exceptions that can be raised during command execution.
These exceptions are caught and handled by the CLI to provide user-friendly error messages.
"""

from typing import Optional

from pepperpy.core.errors import PepperpyError


class CLIError(PepperpyError):
    """Base class for CLI-specific errors."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None) -> None:
        """Initialize the CLI error.

        Args:
            message: The error message.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {"recovery_hint": recovery_hint} if recovery_hint else None
        super().__init__(message, details)


class CommandError(CLIError):
    """Error raised when a command fails to execute."""

    def __init__(
        self, command: str, reason: str, recovery_hint: Optional[str] = None
    ) -> None:
        """Initialize the command error.

        Args:
            command: The command that failed.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        super().__init__(
            f"Command '{command}' failed: {reason}",
            recovery_hint
            or f"Check the command syntax and try again: pepperpy {command} --help",
        )
        self.command = command
        self.reason = reason


class ConfigError(CLIError):
    """Error raised when there are issues with configuration files."""

    def __init__(
        self, file_path: str, reason: str, recovery_hint: Optional[str] = None
    ) -> None:
        """Initialize the config error.

        Args:
            file_path: The path to the config file.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        super().__init__(
            f"Configuration error in '{file_path}': {reason}",
            recovery_hint or "Check the configuration file format and values",
        )
        self.file_path = file_path
        self.reason = reason


class ValidationError(CLIError):
    """Error raised when input validation fails."""

    def __init__(
        self, field: str, reason: str, recovery_hint: Optional[str] = None
    ) -> None:
        """Initialize the validation error.

        Args:
            field: The field that failed validation.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        super().__init__(
            f"Validation error for '{field}': {reason}",
            recovery_hint or f"Check the value provided for '{field}'",
        )
        self.field = field
        self.reason = reason


class ExecutionError(CLIError):
    """Error raised when execution of a component fails."""

    def __init__(
        self,
        component_type: str,
        component_id: str,
        reason: str,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the execution error.

        Args:
            component_type: The type of component (agent, workflow, tool).
            component_id: The ID of the component.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        super().__init__(
            f"Failed to execute {component_type} '{component_id}': {reason}",
            recovery_hint or f"Check the {component_type} configuration and try again",
        )
        self.component_type = component_type
        self.component_id = component_id
        self.reason = reason
