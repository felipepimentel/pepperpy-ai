"""Validation utilities for Pepperpy."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

from ..errors import ValidationError


def validate_positive(
    value: Union[int, float],
    allow_zero: bool = False,
    field_name: Optional[str] = None
) -> None:
    """Validate a numeric value is positive.
    
    Args:
        value: Value to validate
        allow_zero: Whether to allow zero value
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"{field_name or 'Value'} must be a number"
        )
        
    if allow_zero:
        if numeric_value < 0:
            raise ValidationError(
                f"{field_name or 'Value'} must be non-negative"
            )
    else:
        if numeric_value <= 0:
            raise ValidationError(
                f"{field_name or 'Value'} must be positive"
            )


def validate_range(
    value: Union[int, float],
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    inclusive: bool = True,
    field_name: Optional[str] = None
) -> None:
    """Validate a numeric value is within a range.
    
    Args:
        value: Value to validate
        min_value: Optional minimum allowed value
        max_value: Optional maximum allowed value
        inclusive: Whether range bounds are inclusive
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"{field_name or 'Value'} must be a number"
        )
        
    if min_value is not None:
        if inclusive:
            if numeric_value < min_value:
                raise ValidationError(
                    f"{field_name or 'Value'} must be greater than or equal to {min_value}"
                )
        else:
            if numeric_value <= min_value:
                raise ValidationError(
                    f"{field_name or 'Value'} must be greater than {min_value}"
                )
                
    if max_value is not None:
        if inclusive:
            if numeric_value > max_value:
                raise ValidationError(
                    f"{field_name or 'Value'} must be less than or equal to {max_value}"
                )
        else:
            if numeric_value >= max_value:
                raise ValidationError(
                    f"{field_name or 'Value'} must be less than {max_value}"
                )


def validate_string(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Union[str, Pattern[str]]] = None,
    choices: Optional[List[str]] = None,
    field_name: Optional[str] = None
) -> None:
    """Validate a string value.
    
    Args:
        value: String to validate
        min_length: Optional minimum length
        max_length: Optional maximum length
        pattern: Optional regex pattern to match
        choices: Optional list of valid choices
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name or 'Value'} must be a string"
        )
        
    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"{field_name or 'Value'} must be at least {min_length} characters"
        )
        
    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"{field_name or 'Value'} must be at most {max_length} characters"
        )
        
    if pattern is not None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.match(value):
            raise ValidationError(
                f"{field_name or 'Value'} must match pattern {pattern.pattern}"
            )
            
    if choices is not None and value not in choices:
        raise ValidationError(
            f"{field_name or 'Value'} must be one of: {', '.join(choices)}"
        )


def validate_path(
    path: Union[str, Path],
    must_exist: bool = False,
    file_only: bool = False,
    dir_only: bool = False,
    field_name: Optional[str] = None
) -> None:
    """Validate a file system path.
    
    Args:
        path: Path to validate
        must_exist: Whether path must exist
        file_only: Whether path must be a file
        dir_only: Whether path must be a directory
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    if isinstance(path, str):
        path = Path(path)
        
    if must_exist and not path.exists():
        raise ValidationError(
            f"{field_name or 'Path'} does not exist: {path}"
        )
        
    if file_only and path.exists() and not path.is_file():
        raise ValidationError(
            f"{field_name or 'Path'} must be a file: {path}"
        )
        
    if dir_only and path.exists() and not path.is_dir():
        raise ValidationError(
            f"{field_name or 'Path'} must be a directory: {path}"
        )


def validate_dict(
    value: Dict[str, Any],
    required_keys: Optional[List[str]] = None,
    optional_keys: Optional[List[str]] = None,
    field_name: Optional[str] = None
) -> None:
    """Validate a dictionary.
    
    Args:
        value: Dictionary to validate
        required_keys: Optional list of required keys
        optional_keys: Optional list of optional keys
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, dict):
        raise ValidationError(
            f"{field_name or 'Value'} must be a dictionary"
        )
        
    if required_keys:
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise ValidationError(
                f"{field_name or 'Dictionary'} missing required keys: {', '.join(missing_keys)}"
            )
            
    if required_keys or optional_keys:
        allowed_keys = set(required_keys or []) | set(optional_keys or [])
        extra_keys = set(value.keys()) - allowed_keys
        if extra_keys:
            raise ValidationError(
                f"{field_name or 'Dictionary'} contains invalid keys: {', '.join(extra_keys)}"
            ) 