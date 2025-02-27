"""Utilitários para manipulação de dicionários.

Implementa funções auxiliares para manipulação e formatação de dicionários.
"""

from typing import Any, Callable, Dict, List, TypeVar

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


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
                        result[key] = DictUtils.merge(
                            result[key],  # type: ignore
                            value,  # type: ignore
                            deep=True,
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
