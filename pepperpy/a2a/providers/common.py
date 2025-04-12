"""
Common utilities for A2A providers.

This module provides common functionality for A2A providers,
including configuration handling and error utilities.
"""

from typing import Any, Dict

from pepperpy.a2a.base import A2AError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a configuration value.
    
    Args:
        config: Configuration dictionary
        key: Configuration key
        default: Default value if the key is not found
        
    Returns:
        Configuration value or default
    """
    return config.get(key, default)


def has_config_key(config: Dict[str, Any], key: str) -> bool:
    """Check if a configuration key exists.
    
    Args:
        config: Configuration dictionary
        key: Configuration key
        
    Returns:
        True if the key exists, False otherwise
    """
    return key in config


def update_config(config: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """Update the configuration.
    
    Args:
        config: Configuration dictionary
        **kwargs: Configuration values to update
        
    Returns:
        Updated configuration dictionary
    """
    config.update(kwargs)
    return config


def convert_exception(e: Exception, message: str) -> A2AError:
    """Convert an exception to an A2AError.
    
    Args:
        e: Original exception
        message: Error message
        
    Returns:
        A2AError with the original exception as cause
    """
    if isinstance(e, A2AError):
        return e
    return A2AError(f"{message}: {e}") from e

# End of file 