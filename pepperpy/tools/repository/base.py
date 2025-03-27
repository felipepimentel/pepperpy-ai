"""Base interfaces for repository tools.

This module defines the common interfaces for repository-related tools
and providers, establishing the contracts that implementations must follow.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.core.base import BaseProvider
from pepperpy.tools.base import ToolError


class RepositoryError(ToolError):
    """Error related to repository operations."""

    pass


class RepositoryProvider(BaseProvider):
    """Base interface for repository providers.

    Repository providers connect to repository hosting services
    (like GitHub, GitLab) or local file systems to access repository data.
    """

    @abstractmethod
    async def get_repository(self, repo_identifier: str) -> Dict[str, Any]:
        """Get repository data by identifier.

        Args:
            repo_identifier: Repository identifier, format depends on provider
                (e.g., "username/repo" for GitHub)

        Returns:
            Repository data dictionary

        Raises:
            RepositoryError: If repository cannot be accessed
        """
        pass

    @abstractmethod
    async def get_files(
        self, repo_identifier: str, path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get file list from repository.

        Args:
            repo_identifier: Repository identifier
            path: Optional path within repository

        Returns:
            List of file metadata dictionaries

        Raises:
            RepositoryError: If files cannot be accessed
        """
        pass

    @abstractmethod
    async def get_file_content(self, repo_identifier: str, file_path: str) -> str:
        """Get content of a specific file.

        Args:
            repo_identifier: Repository identifier
            file_path: Path to file within repository

        Returns:
            File content as string

        Raises:
            RepositoryError: If file cannot be accessed
        """
        pass

    @abstractmethod
    async def get_commits(
        self, repo_identifier: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get commit history for repository.

        Args:
            repo_identifier: Repository identifier
            limit: Optional limit on number of commits to retrieve

        Returns:
            List of commit metadata dictionaries

        Raises:
            RepositoryError: If commits cannot be accessed
        """
        pass
