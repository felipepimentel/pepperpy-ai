"""Tools for integrating PepperPy with external services and platforms.

This module provides tool interfaces and implementations for connecting 
to various external services like GitHub, GitLab, Google Drive, etc.

The tools are organized by service type:
- repository: Tools for analyzing code repositories
- storage: Tools for handling cloud storage
- email: Tools for email integration

Example:
    >>> from pepperpy.tools.repository import RepositoryAnalyzer
    >>> from pepperpy.tools.repository.providers import GitHubProvider
    >>> analyzer = RepositoryAnalyzer(provider=GitHubProvider(token="your_token"))
    >>> report = await analyzer.analyze("username/repo")
"""

from pepperpy.tools.base import BaseTool

__all__ = [
    "BaseTool",
] 