"""Utilitários para manipulação de listas (DEPRECATED).

Implementa funções auxiliares para manipulação e formatação de listas.

This module is deprecated and will be removed in version 1.0.0.
Please use 'pepperpy.core.utils.collections.ListUtils' instead.
"""

import warnings
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")


# Show deprecation warning
warnings.warn(
    "The 'pepperpy.core.utils.lists' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.core.utils.collections.ListUtils' instead.",
    DeprecationWarning,
    stacklevel=2,
)


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
    def group_by(items: List[T], key: Callable[[T], U]) -> dict[U, List[T]]:
        """Group list items by key function.

        Args:
            items: List to group
            key: Function to get group key

        Returns:
            Dictionary of grouped items
        """
        result: dict[U, List[T]] = {}
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
