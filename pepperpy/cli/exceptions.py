"""Exceptions for the Pepperpy CLI.

This module defines CLI-specific exceptions that can be raised during command execution.
These exceptions are caught and handled by the CLI to provide user-friendly error messages.
"""

from pepperpy.common.errors import PepperError


class CLIError(PepperError):
    """Base class for CLI-specific errors."""

    def __init__(self, message: str, recovery_hint: str | None = None) -> None:
        """Initialize the CLI error.

        Args:
            message: The error message.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {"recovery_hint": recovery_hint} if recovery_hint else {}
        details["error_code"] = "CLI000"
        super().__init__(message, details=details)


class CommandError(CLIError):
    """Error raised when a command fails to execute."""

    def __init__(
        self, command: str, reason: str, recovery_hint: str | None = None
    ) -> None:
        """Initialize the command error.

        Args:
            command: The command that failed.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {
            "command": command,
            "reason": reason,
            "error_code": "CLI001",
            "recovery_hint": recovery_hint
            or f"Check the command syntax and try again: pepperpy {command} --help",
        }
        super().__init__(
            f"Command '{command}' failed: {reason}",
            details["recovery_hint"],
        )
        self.details = details


class ConfigError(CLIError):
    """Error raised when there are issues with configuration files."""

    def __init__(
        self, file_path: str, reason: str, recovery_hint: str | None = None
    ) -> None:
        """Initialize the config error.

        Args:
            file_path: The path to the config file.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {
            "file_path": file_path,
            "reason": reason,
            "error_code": "CLI002",
            "recovery_hint": recovery_hint
            or "Check the configuration file format and values",
        }
        super().__init__(
            f"Configuration error in '{file_path}': {reason}",
            details["recovery_hint"],
        )
        self.details = details


class ValidationError(CLIError):
    """Error raised when input validation fails."""

    def __init__(
        self, field: str, reason: str, recovery_hint: str | None = None
    ) -> None:
        """Initialize the validation error.

        Args:
            field: The field that failed validation.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {
            "field": field,
            "reason": reason,
            "error_code": "CLI003",
            "recovery_hint": recovery_hint or f"Check the value provided for '{field}'",
        }
        super().__init__(
            f"Validation error for '{field}': {reason}",
            details["recovery_hint"],
        )
        self.details = details


class ExecutionError(CLIError):
    """Error raised when execution of a component fails."""

    def __init__(
        self,
        component_type: str,
        component_id: str,
        reason: str,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize the execution error.

        Args:
            component_type: The type of component that failed.
            component_id: The ID of the component that failed.
            reason: The reason for the failure.
            recovery_hint: Optional hint for recovering from the error.
        """
        details = {
            "component_type": component_type,
            "component_id": component_id,
            "reason": reason,
            "error_code": "CLI004",
            "recovery_hint": recovery_hint
            or f"Check the {component_type} configuration and try again",
        }
        super().__init__(
            f"Execution of {component_type} '{component_id}' failed: {reason}",
            details["recovery_hint"],
        )
        self.details = details
