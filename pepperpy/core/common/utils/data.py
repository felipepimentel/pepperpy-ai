"""Data manipulation utilities.

Implements helper functions for data manipulation and conversion.
"""

import json
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
)

T = TypeVar("T")


class HasFromDict(Protocol):
    """Protocol for classes with from_dict method."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Create instance from dictionary."""
        ...


class HasParseObj(Protocol):
    """Protocol for classes with parse_obj method."""

    @classmethod
    def parse_obj(cls, data: Dict[str, Any]) -> Any:
        """Create instance from dictionary."""
        ...


class DataUtils:
    """Utility functions for data manipulation."""

    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary.

        Args:
            obj: Object to convert

        Returns:
            Dictionary representation

        """
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, dict):
            return obj
        raise ValueError(f"Cannot convert {type(obj)} to dict")

    @staticmethod
    def from_dict(data: Dict[str, Any], cls: Type[T]) -> T:
        """Create object from dictionary.

        Args:
            data: Dictionary data
            cls: Target class

        Returns:
            Instance of target class

        """
        if hasattr(cls, "from_dict"):
            return cast(HasFromDict, cls).from_dict(data)
        if hasattr(cls, "parse_obj"):
            return cast(HasParseObj, cls).parse_obj(data)
        return cls(**data)

    @staticmethod
    def to_json(obj: Any) -> str:
        """Convert object to JSON string.

        Args:
            obj: Object to convert

        Returns:
            JSON string

        """

        def default(o: Any) -> Any:
            if isinstance(o, datetime):
                return o.isoformat()
            return str(o)

        return json.dumps(DataUtils.to_dict(obj), default=default)

    @staticmethod
    def from_json(data: str, cls: Type[T]) -> T:
        """Create object from JSON string.

        Args:
            data: JSON string
            cls: Target class

        Returns:
            Instance of target class

        """
        return DataUtils.from_dict(json.loads(data), cls)

    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
        """Merge multiple dictionaries.

        Args:
            *dicts: Dictionaries to merge
            overwrite: Whether to overwrite existing keys

        Returns:
            Merged dictionary

        """
        result = {}
        for d in dicts:
            if overwrite:
                result.update(d)
            else:
                result.update({k: v for k, v in d.items() if k not in result})
        return result

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = ".",
    ) -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested items
            sep: Separator for nested keys

        Returns:
            Flattened dictionary

        """
        items: List[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


def transform_data(
    data: Any,
    transformers: Union[Callable[[Any], Any], List[Callable[[Any], Any]]],
    error_handler: Optional[Callable[[Exception, Any], Any]] = None,
) -> Any:
    """Apply one or more transformation functions to data.

    This function applies a series of transformation functions to the input data.
    Each transformer is applied in sequence, with the output of one transformer
    becoming the input to the next.

    Args:
        data: The input data to transform
        transformers: A single transformer function or a list of transformer functions
        error_handler: Optional function to handle exceptions during transformation

    Returns:
        The transformed data

    Examples:
        >>> def add_one(x): return x + 1
        >>> def multiply_by_two(x): return x * 2
        >>> transform_data(5, [add_one, multiply_by_two])
        12
        >>> transform_data(5, add_one)
        6
    """
    if not callable(transformers) and not isinstance(transformers, list):
        raise TypeError("transformers must be a callable or list of callables")

    # Convert single transformer to list for uniform processing
    if callable(transformers):
        transformers = [transformers]

    result = data
    for transformer in transformers:
        try:
            result = transformer(result)
        except Exception as e:
            if error_handler:
                result = error_handler(e, result)
            else:
                raise

    return result


def validate_data(
    data: Any,
    validators: Union[Callable[[Any], bool], List[Callable[[Any], bool]]],
    error_handler: Optional[Callable[[Exception, Any], Any]] = None,
) -> bool:
    """Validate data using one or more validator functions.

    This function applies a series of validation functions to the input data.
    All validators must return True for the data to be considered valid.

    Args:
        data: The input data to validate
        validators: A single validator function or a list of validator functions
        error_handler: Optional function to handle exceptions during validation

    Returns:
        True if all validators pass, False otherwise

    Examples:
        >>> def is_positive(x): return x > 0
        >>> def is_even(x): return x % 2 == 0
        >>> validate_data(4, [is_positive, is_even])
        True
        >>> validate_data(3, [is_positive, is_even])
        False
    """
    if not callable(validators) and not isinstance(validators, list):
        raise TypeError("validators must be a callable or list of callables")

    # Convert single validator to list for uniform processing
    if callable(validators):
        validators = [validators]

    for validator in validators:
        try:
            if not validator(data):
                return False
        except Exception as e:
            if error_handler:
                if not error_handler(e, data):
                    return False
            else:
                raise

    return True
