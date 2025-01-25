"""Configuration-specific error classes."""

from ...common.errors import PepperpyError


class ConfigError(PepperpyError):
    """Error raised when there is a configuration issue."""
    pass


class ValidationError(PepperpyError):
    """Error raised when there is a validation issue."""
    pass


class LoadError(PepperpyError):
    """Error raised when there is an issue loading a configuration."""
    pass


class SaveError(PepperpyError):
    """Error raised when there is an issue saving a configuration."""
    pass 