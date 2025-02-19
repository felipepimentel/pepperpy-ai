"""Framework adapter errors.

This module defines custom exceptions for framework adapters.
"""


class AdapterError(Exception):
    """Base class for adapter errors."""

    pass


class ConversionError(AdapterError):
    """Error converting between Pepperpy and framework types."""

    pass


class ConfigurationError(AdapterError):
    """Error in adapter configuration."""

    pass


class ValidationError(AdapterError):
    """Error validating adapter data."""

    pass
