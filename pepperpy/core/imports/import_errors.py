"""Import-related error classes."""


class ImportError(Exception):
    """Base class for import-related errors."""

    def __init__(self, message: str) -> None:
        """Initialize error.

        Args:
            message: Error message

        """
        super().__init__(message)


class CircularDependencyError(ImportError):
    """Error raised when a circular dependency is detected."""

    def __init__(self, module: str, chain: list[str]) -> None:
        """Initialize error.

        Args:
            module: Module name where circular dependency was detected
            chain: Chain of imports leading to circular dependency

        """
        super().__init__(
            f"Circular dependency detected for module {module}: {' -> '.join(chain)}",
        )
        self.module = module
        self.chain = chain


class ImportValidationError(ImportError):
    """Error raised when import validation fails."""

    def __init__(self, module: str, reason: str) -> None:
        """Initialize error.

        Args:
            module: Module name that failed validation
            reason: Reason for validation failure

        """
        super().__init__(f"Import validation failed for {module}: {reason}")
        self.module = module
        self.reason = reason
