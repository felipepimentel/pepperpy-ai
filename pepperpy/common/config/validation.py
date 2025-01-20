"""Validation utilities for configuration."""

from typing import Any, Optional, Tuple

from .base import ConfigError


class ValidationMixin:
    """Mixin providing common validation methods."""
    
    def validate_positive(
        self,
        field_name: str,
        value: Any,
        allow_zero: bool = False
    ) -> None:
        """Validate a value is positive.
        
        Args:
            field_name: Name of field being validated.
            value: Value to validate.
            allow_zero: Whether to allow zero value.
            
        Raises:
            ConfigError: If validation fails.
        """
        if value is None:
            return
            
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ConfigError(f"{field_name} must be a number")
            
        if allow_zero:
            if numeric_value < 0:
                raise ConfigError(f"{field_name} must be non-negative")
        else:
            if numeric_value <= 0:
                raise ConfigError(f"{field_name} must be positive")
    
    def validate_range(
        self,
        field_name: str,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True
    ) -> None:
        """Validate a value is within a range.
        
        Args:
            field_name: Name of field being validated.
            value: Value to validate.
            min_value: Minimum allowed value.
            max_value: Maximum allowed value.
            inclusive: Whether range bounds are inclusive.
            
        Raises:
            ConfigError: If validation fails.
        """
        if value is None:
            return
            
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ConfigError(f"{field_name} must be a number")
            
        if min_value is not None:
            if inclusive:
                if numeric_value < min_value:
                    raise ConfigError(
                        f"{field_name} must be greater than or equal to {min_value}"
                    )
            else:
                if numeric_value <= min_value:
                    raise ConfigError(
                        f"{field_name} must be greater than {min_value}"
                    )
                    
        if max_value is not None:
            if inclusive:
                if numeric_value > max_value:
                    raise ConfigError(
                        f"{field_name} must be less than or equal to {max_value}"
                    )
            else:
                if numeric_value >= max_value:
                    raise ConfigError(
                        f"{field_name} must be less than {max_value}"
                    )
    
    def validate_string(
        self,
        field_name: str,
        value: Any,
        choices: Optional[Tuple[str, ...]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> None:
        """Validate a string value.
        
        Args:
            field_name: Name of field being validated.
            value: Value to validate.
            choices: Allowed string values.
            min_length: Minimum string length.
            max_length: Maximum string length.
            
        Raises:
            ConfigError: If validation fails.
        """
        if value is None:
            return
            
        if not isinstance(value, str):
            raise ConfigError(f"{field_name} must be a string")
            
        if choices and value not in choices:
            raise ConfigError(
                f"{field_name} must be one of: {', '.join(choices)}"
            )
            
        if min_length is not None and len(value) < min_length:
            raise ConfigError(
                f"{field_name} must be at least {min_length} characters"
            )
            
        if max_length is not None and len(value) > max_length:
            raise ConfigError(
                f"{field_name} must be at most {max_length} characters"
            ) 