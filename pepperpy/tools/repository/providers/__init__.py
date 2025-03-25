"""Repository provider implementations for PepperPy.

This module provides implementations for connecting to various repository
providers such as GitHub, GitLab, and local filesystems.

Example:
    >>> from pepperpy.tools.repository.providers import GitHubProvider
    >>> provider = GitHubProvider(token="your_token")
    >>> await provider.connect()
    >>> repo = await provider.get_repository("username/repo")
"""

from pepperpy.tools.repository.base import RepositoryProvider
from pepperpy.tools.repository.providers.github import GitHubProvider
# The following imports will be uncommented when the implementations are created
# from pepperpy.tools.repository.providers.gitlab import GitLabProvider
# from pepperpy.tools.repository.providers.filesystem import FilesystemProvider

__all__ = [
    "RepositoryProvider",
    "GitHubProvider",
    # "GitLabProvider",
    # "FilesystemProvider",
] 