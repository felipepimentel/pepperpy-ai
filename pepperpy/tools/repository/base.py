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
    async def list_repository_files(
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
    async def read_repository_file(self, repo_identifier: str, file_path: str) -> str:
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

    @abstractmethod
    async def clone(self, url: str, branch: Optional[str] = None) -> str:
        """Clone a repository.

        Args:
            url: Repository URL
            branch: Optional branch to clone

        Returns:
            Path to cloned repository
        """
        pass

    @abstractmethod
    async def get_files(self, path: Optional[str] = None) -> List[str]:
        """Get list of files in repository.

        Args:
            path: Optional path to list files from

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    async def get_file_content(self, path: str) -> str:
        """Get content of a file.

        Args:
            path: Path to file

        Returns:
            File content as string
        """
        pass


def create_provider(provider_type: str = "github", **config: Any) -> RepositoryProvider:
    """Create a Repository provider based on type.

    Args:
        provider_type: Type of provider to create (default: github)
        **config: Provider configuration

    Returns:
        An instance of the specified RepositoryProvider

    Raises:
        ValidationError: If provider creation fails
    """
    try:
        import importlib

        # Import provider module
        module_name = f"pepperpy.tools.repository.{provider_type}"
        module = importlib.import_module(module_name)

        # Get provider class
        provider_class_name = f"{provider_type.title()}Provider"
        provider_class = getattr(module, provider_class_name)

        # Create provider instance
        return provider_class(**config)
    except (ImportError, AttributeError) as e:
        from pepperpy.core.base import ValidationError

        raise ValidationError(
            f"Failed to create Repository provider '{provider_type}': {e}"
        )
