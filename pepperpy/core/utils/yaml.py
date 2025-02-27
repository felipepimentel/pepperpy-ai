"""Utilitários para manipulação de arquivos YAML.

Implementa funções auxiliares para manipulação e formatação de arquivos YAML.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml


class YamlUtils:
    """Utility functions for YAML manipulation."""

    @staticmethod
    def load(path: Union[str, Path]) -> Any:
        """Load YAML from file.

        Args:
            path: File path

        Returns:
            Parsed YAML data
        """
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def save(
        data: Any, path: Union[str, Path], default_flow_style: bool = False
    ) -> None:
        """Save data to YAML file.

        Args:
            data: Data to save
            path: File path
            default_flow_style: Whether to use flow style
        """
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=default_flow_style,
                allow_unicode=True,
                sort_keys=False,
                default_style=None,
                indent=2,
                width=80,
                encoding="utf-8",
            )

    @staticmethod
    def dumps(data: Any, default_flow_style: bool = False) -> str:
        """Convert data to YAML string.

        Args:
            data: Data to convert
            default_flow_style: Whether to use flow style

        Returns:
            YAML string
        """
        return yaml.dump(
            data,
            default_flow_style=default_flow_style,
            allow_unicode=True,
            sort_keys=False,
            default_style=None,
            indent=2,
            width=80,
            encoding=None,
        )

    @staticmethod
    def loads(data: str) -> Any:
        """Parse YAML string.

        Args:
            data: YAML string

        Returns:
            Parsed data
        """
        return yaml.safe_load(data)

    @staticmethod
    def merge(*yamls: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
        """Merge multiple YAML objects.

        Args:
            *yamls: YAML objects to merge
            deep: Whether to perform deep merge

        Returns:
            Merged YAML object
        """
        result: Dict[str, Any] = {}

        for data in yamls:
            if not deep:
                result.update(data)
            else:
                for key, value in data.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = YamlUtils.merge(result[key], value, deep=True)
                    else:
                        result[key] = value

        return result

    @staticmethod
    def flatten(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested YAML object.

        Args:
            data: YAML object to flatten
            parent_key: Parent key for nested items
            separator: Key separator

        Returns:
            Flattened YAML object
        """
        items: List[tuple[str, Any]] = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    YamlUtils.flatten(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten YAML object with dot notation keys.

        Args:
            data: Flattened YAML object
            separator: Key separator

        Returns:
            Nested YAML object
        """
        result: Dict[str, Any] = {}

        for key, value in data.items():
            parts = key.split(separator)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    @staticmethod
    def to_json(data: Any) -> str:
        """Convert YAML to JSON string.

        Args:
            data: YAML data

        Returns:
            JSON string
        """
        return yaml.dump(
            data, default_flow_style=True, allow_unicode=True, sort_keys=False
        )

    @staticmethod
    def from_json(data: str) -> Any:
        """Convert JSON string to YAML.

        Args:
            data: JSON string

        Returns:
            YAML data
        """
        return yaml.safe_load(data)
