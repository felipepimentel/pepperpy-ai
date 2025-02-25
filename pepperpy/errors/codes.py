"""Error code definitions for the Pepperpy error handling system."""

from enum import Enum


class ErrorCategory(Enum):
    """Categories for error codes."""

    VALIDATION = "VAL"
    RESOURCE = "RES"
    CONFIG = "CFG"
    STATE = "STA"
    SECURITY = "SEC"
    NETWORK = "NET"
    DATABASE = "DB"
    SYSTEM = "SYS"


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    CRITICAL = "C"
    FATAL = "F"


def generate_error_code(
    category: ErrorCategory, severity: ErrorSeverity, code: int
) -> str:
    """Generate a unique error code.

    Format: CAT-SEV-XXX (e.g., VAL-E-001)
    """
    return f"{category.value}-{severity.value}-{code:03d}"


# Common error codes
VALIDATION_ERRORS = {
    "INVALID_INPUT": generate_error_code(
        ErrorCategory.VALIDATION, ErrorSeverity.ERROR, 1
    ),
    "MISSING_REQUIRED": generate_error_code(
        ErrorCategory.VALIDATION, ErrorSeverity.ERROR, 2
    ),
    "TYPE_MISMATCH": generate_error_code(
        ErrorCategory.VALIDATION, ErrorSeverity.ERROR, 3
    ),
}

RESOURCE_ERRORS = {
    "NOT_FOUND": generate_error_code(ErrorCategory.RESOURCE, ErrorSeverity.ERROR, 1),
    "ALREADY_EXISTS": generate_error_code(
        ErrorCategory.RESOURCE, ErrorSeverity.ERROR, 2
    ),
    "ACCESS_DENIED": generate_error_code(
        ErrorCategory.RESOURCE, ErrorSeverity.ERROR, 3
    ),
}

CONFIG_ERRORS = {
    "INVALID_CONFIG": generate_error_code(ErrorCategory.CONFIG, ErrorSeverity.ERROR, 1),
    "MISSING_CONFIG": generate_error_code(ErrorCategory.CONFIG, ErrorSeverity.ERROR, 2),
    "CONFIG_LOAD_ERROR": generate_error_code(
        ErrorCategory.CONFIG, ErrorSeverity.ERROR, 3
    ),
}

STATE_ERRORS = {
    "INVALID_STATE": generate_error_code(ErrorCategory.STATE, ErrorSeverity.ERROR, 1),
    "STATE_TRANSITION": generate_error_code(
        ErrorCategory.STATE, ErrorSeverity.ERROR, 2
    ),
}

# Error code registry
ERROR_CODES: dict[str, str] = {
    **VALIDATION_ERRORS,
    **RESOURCE_ERRORS,
    **CONFIG_ERRORS,
    **STATE_ERRORS,
}
