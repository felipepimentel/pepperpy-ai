"""Collection utilities for PepperPy.

This module provides utilities for working with various collection types:
- Lists: List manipulation and operations
- Dictionaries: Dictionary manipulation and nested operations
- Strings: String manipulation and formatting

The module centralizes collection-related functionality to provide a consistent interface
for working with different data structures throughout the framework.
"""

import re
import unicodedata
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
V = TypeVar("V")


class StringUtils:
    """Utility functions for string manipulation."""

    @staticmethod
    def is_empty(text: Optional[str]) -> bool:
        """Check if string is empty.

        Args:
            text: String to check

        Returns:
            True if string is None or empty
        """
        return text is None or text.strip() == ""

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to maximum length.

        Args:
            text: String to truncate
            max_length: Maximum length
            suffix: Suffix to append if truncated

        Returns:
            Truncated string
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def slugify(text: str) -> str:
        """Convert string to slug format.

        Args:
            text: String to convert

        Returns:
            Slug string
        """
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.strip("-")

    @staticmethod
    def camel_to_snake(text: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            text: String to convert

        Returns:
            snake_case string
        """
        pattern = re.compile(r"(?<!^)(?=[A-Z])")
        return pattern.sub("_", text).lower()

    @staticmethod
    def snake_to_camel(text: str) -> str:
        """Convert snake_case to camelCase.

        Args:
            text: String to convert

        Returns:
            camelCase string
        """
        components = text.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def split_words(text: str) -> List[str]:
        """Split string into words.

        Args:
            text: String to split

        Returns:
            List of words
        """
        return [w for w in re.split(r"\W+", text) if w]

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in string.

        Args:
            text: String to normalize

        Returns:
            Normalized string
        """
        return " ".join(text.split())

    @staticmethod
    def remove_accents(text: str) -> str:
        """Remove accents from string.

        Args:
            text: String to process

        Returns:
            String without accents
        """
        return "".join(
            c
            for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract numbers from string.

        Args:
            text: String to process

        Returns:
            List of numbers
        """
        return re.findall(r"\d+", text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from string.

        Args:
            text: String to process

        Returns:
            List of email addresses
        """
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(pattern, text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from string.

        Args:
            text: String to process

        Returns:
            List of URLs
        """
        pattern = (
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|"
            r"[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        return re.findall(pattern, text)


class ListUtils:
    """Utility functions for list manipulation."""

    @staticmethod
    def chunk(items: List[T], size: int) -> List[List[T]]:
        """Split list into chunks.

        Args:
            items: List to split
            size: Chunk size

        Returns:
            List of chunks
        """
        return [items[i : i + size] for i in range(0, len(items), size)]

    @staticmethod
    def flatten(items: List[Any], depth: Optional[int] = None) -> List[Any]:
        """Flatten nested list.

        Args:
            items: List to flatten
            depth: Maximum depth to flatten

        Returns:
            Flattened list
        """
        result = []
        for item in items:
            if isinstance(item, list) and (depth is None or depth > 0):
                result.extend(
                    ListUtils.flatten(item, None if depth is None else depth - 1)
                )
            else:
                result.append(item)
        return result

    @staticmethod
    def unique(items: List[T]) -> List[T]:
        """Remove duplicate items from list.

        Args:
            items: List to process

        Returns:
            List without duplicates
        """
        return list(dict.fromkeys(items))

    @staticmethod
    def group_by(items: List[T], key: Callable[[T], U]) -> Dict[U, List[T]]:
        """Group list items by key function.

        Args:
            items: List to group
            key: Function to get group key

        Returns:
            Dictionary of grouped items
        """
        result: Dict[U, List[T]] = {}
        for item in items:
            k = key(item)
            if k not in result:
                result[k] = []
            result[k].append(item)
        return result

    @staticmethod
    def partition(
        items: List[T], predicate: Callable[[T], bool]
    ) -> tuple[List[T], List[T]]:
        """Split list into two parts based on predicate.

        Args:
            items: List to split
            predicate: Function to test items

        Returns:
            Tuple of (matching, non-matching) items
        """
        matching = []
        non_matching = []
        for item in items:
            if predicate(item):
                matching.append(item)
            else:
                non_matching.append(item)
        return matching, non_matching

    @staticmethod
    def find_index(items: List[T], predicate: Callable[[T], bool]) -> Optional[int]:
        """Find index of first item matching predicate.

        Args:
            items: List to search
            predicate: Function to test items

        Returns:
            Index of matching item or None
        """
        for i, item in enumerate(items):
            if predicate(item):
                return i
        return None

    @staticmethod
    def find(items: List[T], predicate: Callable[[T], bool]) -> Optional[T]:
        """Find first item matching predicate.

        Args:
            items: List to search
            predicate: Function to test items

        Returns:
            Matching item or None
        """
        index = ListUtils.find_index(items, predicate)
        return items[index] if index is not None else None

    @staticmethod
    def count_by(items: List[T], predicate: Callable[[T], bool]) -> int:
        """Count items matching predicate.

        Args:
            items: List to count
            predicate: Function to test items

        Returns:
            Number of matching items
        """
        return sum(1 for item in items if predicate(item))

    @staticmethod
    def all_match(items: List[T], predicate: Callable[[T], bool]) -> bool:
        """Check if all items match predicate.

        Args:
            items: List to check
            predicate: Function to test items

        Returns:
            True if all items match
        """
        return all(predicate(item) for item in items)

    @staticmethod
    def any_match(items: List[T], predicate: Callable[[T], bool]) -> bool:
        """Check if any item matches predicate.

        Args:
            items: List to check
            predicate: Function to test items

        Returns:
            True if any item matches
        """
        return any(predicate(item) for item in items)

    @staticmethod
    def remove_by(items: List[T], predicate: Callable[[T], bool]) -> List[T]:
        """Remove items matching predicate.

        Args:
            items: List to process
            predicate: Function to test items

        Returns:
            List without matching items
        """
        return [item for item in items if not predicate(item)]

    @staticmethod
    def update_by(
        items: List[T], predicate: Callable[[T], bool], update: Callable[[T], T]
    ) -> List[T]:
        """Update items matching predicate.

        Args:
            items: List to process
            predicate: Function to test items
            update: Function to update items

        Returns:
            List with updated items
        """
        return [update(item) if predicate(item) else item for item in items]


class DictUtils:
    """Utility functions for dictionary manipulation."""

    @staticmethod
    def get_nested(
        data: Dict[str, Any], path: str, default: Any = None, separator: str = "."
    ) -> Any:
        """Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Path to value using dot notation
            default: Default value if not found
            separator: Path separator

        Returns:
            Value at path or default
        """
        keys = path.split(separator)
        current = data

        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default

        return current

    @staticmethod
    def set_nested(
        data: Dict[str, Any], path: str, value: Any, separator: str = "."
    ) -> None:
        """Set value in nested dictionary using dot notation.

        Args:
            data: Dictionary to modify
            path: Path to value using dot notation
            value: Value to set
            separator: Path separator
        """
        keys = path.split(separator)
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def delete_nested(data: Dict[str, Any], path: str, separator: str = ".") -> None:
        """Delete value from nested dictionary using dot notation.

        Args:
            data: Dictionary to modify
            path: Path to value using dot notation
            separator: Path separator
        """
        keys = path.split(separator)
        current = data

        for key in keys[:-1]:
            if not isinstance(current, dict) or key not in current:
                return
            current = current[key]

        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]

    @staticmethod
    def merge(*dicts: Dict[K, V], deep: bool = False) -> Dict[K, V]:
        """Merge multiple dictionaries.

        Args:
            *dicts: Dictionaries to merge
            deep: Whether to perform deep merge

        Returns:
            Merged dictionary
        """
        result: Dict[K, V] = {}

        for d in dicts:
            if not deep:
                result.update(d)
            else:
                for key, value in d.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        # Type ignore is needed because mypy can't infer that both are dicts  # noqa: E501
                        result[key] = cast(
                            V,
                            DictUtils.merge(
                                cast(Dict[K, V], result[key]),
                                cast(Dict[K, V], value),
                                deep=True,
                            ),
                        )
                    else:
                        result[key] = value

        return result

    @staticmethod
    def flatten(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            data: Dictionary to flatten
            parent_key: Parent key for nested items
            separator: Key separator

        Returns:
            Flattened dictionary
        """
        items: List[tuple[str, Any]] = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    DictUtils.flatten(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten dictionary with dot notation keys.

        Args:
            data: Flattened dictionary
            separator: Key separator

        Returns:
            Nested dictionary
        """
        result: Dict[str, Any] = {}

        for key, value in data.items():
            DictUtils.set_nested(result, key, value, separator)

        return result

    @staticmethod
    def filter_keys(
        data: Dict[K, V], keys: List[K], include: bool = True
    ) -> Dict[K, V]:
        """Filter dictionary by keys.

        Args:
            data: Dictionary to filter
            keys: Keys to include/exclude
            include: Whether to include or exclude keys

        Returns:
            Filtered dictionary
        """
        if include:
            return {k: v for k, v in data.items() if k in keys}
        return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def filter_values(data: Dict[K, V], predicate: Callable[[V], bool]) -> Dict[K, V]:
        """Filter dictionary by value predicate.

        Args:
            data: Dictionary to filter
            predicate: Function to filter values

        Returns:
            Filtered dictionary
        """
        return {k: v for k, v in data.items() if predicate(v)}

    @staticmethod
    def map_values(data: Dict[K, V], func: Callable[[V], T]) -> Dict[K, T]:
        """Map dictionary values through function.

        Args:
            data: Dictionary to map
            func: Function to apply to values

        Returns:
            Mapped dictionary
        """
        return {k: func(v) for k, v in data.items()}


# Export all types
__all__ = [
    "StringUtils",
    "ListUtils",
    "DictUtils",
]
