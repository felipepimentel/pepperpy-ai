"""GitHub component module."""

from typing import Dict, List, Optional

from pepperpy.core.base import BaseComponent
from pepperpy.core.config import Config
from pepperpy.github import GitHubClient


class GitHubComponent(BaseComponent):
    """GitHub component for repository operations."""

    def __init__(self, config: Config) -> None:
        """Initialize GitHub component.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._client: Optional[GitHubClient] = None

    async def _initialize(self) -> None:
        """Initialize the GitHub client."""
        self._client = self.config.load_github_client()
        await self._client.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.cleanup()

    async def get_repository(self, repo_identifier: str) -> Dict:
        """Get repository information.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")

        Returns:
            Repository information
        """
        if not self._client:
            await self.initialize()
        return await self._client.get_repository(repo_identifier)

    async def get_files(self, repo_identifier: str) -> List[Dict]:
        """Get repository files.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")

        Returns:
            List of file information
        """
        if not self._client:
            await self.initialize()
        return await self._client.get_files(repo_identifier)

    async def get_file_content(self, repo_identifier: str, file_path: str) -> str:
        """Get file content.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")
            file_path: Path to file in repository

        Returns:
            File content
        """
        if not self._client:
            await self.initialize()
        return await self._client.get_file_content(repo_identifier, file_path)
