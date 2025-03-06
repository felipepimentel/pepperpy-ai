"""Sources namespace for PepperPy.

This module provides a namespace for accessing source components.
"""

from typing import Any, Dict


class SourcesNamespace:
    """Namespace for source components."""

    def __init__(self):
        """Initialize the sources namespace."""
        pass

    def text(self, content: str) -> Dict[str, Any]:
        """Create a text source.

        Args:
            content: The text content

        Returns:
            A source configuration
        """
        return {"type": "text", "content": content}

    def file(self, path: str) -> Dict[str, Any]:
        """Create a file source.

        Args:
            path: Path to the file

        Returns:
            A source configuration
        """
        return {"type": "file", "path": path}

    def url(self, url: str) -> Dict[str, Any]:
        """Create a URL source.

        Args:
            url: The URL to fetch

        Returns:
            A source configuration
        """
        return {"type": "url", "url": url}

    def database(self, query: str, connection: str) -> Dict[str, Any]:
        """Create a database source.

        Args:
            query: SQL query to execute
            connection: Database connection string

        Returns:
            A source configuration
        """
        return {"type": "database", "query": query, "connection": connection}

    def rss(self, url: str, max_items: int = 10) -> Dict[str, Any]:
        """Create an RSS source.

        Args:
            url: URL of the RSS feed
            max_items: Maximum number of items to fetch

        Returns:
            A source configuration
        """
        return {"type": "rss", "url": url, "max_items": max_items}


# Create a singleton instance
sources = SourcesNamespace()
