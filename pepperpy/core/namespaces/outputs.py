"""Outputs namespace for PepperPy.

This module provides a namespace for accessing output components.
"""

from typing import Any, Dict


class OutputsNamespace:
    """Namespace for output components."""

    def __init__(self):
        """Initialize the outputs namespace."""
        pass

    def console(self, format: str = "text") -> Dict[str, Any]:
        """Create a console output.

        Args:
            format: Output format (text, json, yaml)

        Returns:
            An output configuration
        """
        return {"type": "console", "format": format}

    def file(self, path: str, format: str = "text") -> Dict[str, Any]:
        """Create a file output.

        Args:
            path: Path to the output file
            format: Output format (text, json, yaml)

        Returns:
            An output configuration
        """
        return {"type": "file", "path": path, "format": format}

    def database(self, table: str, connection: str) -> Dict[str, Any]:
        """Create a database output.

        Args:
            table: Table to write to
            connection: Database connection string

        Returns:
            An output configuration
        """
        return {"type": "database", "table": table, "connection": connection}

    def memory(self) -> Dict[str, Any]:
        """Create a memory output.

        Returns:
            An output configuration
        """
        return {"type": "memory"}


# Create a singleton instance
outputs = OutputsNamespace()
