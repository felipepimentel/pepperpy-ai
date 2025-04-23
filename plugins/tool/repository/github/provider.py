"""GitHub repository provider implementation."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import dict, list, set, Optional, Any

from pepperpy.tool import ToolProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.tool.repository.base import RepositoryError, RepositoryProvider
from pepperpy.tool.base import ToolError
from pepperpy.tool.base import ToolError

logger = logger.getLogger(__name__)


class GitHubProvider(class GitHubProvider(ToolProvider, ProviderPlugin):
    """GitHub repository provider implementation."""):
    """
    Tool github provider.
    
    This provider implements github functionality for the PepperPy tool framework.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        # Always call base initialize first
        await super().initialize()

        # Check for token in config or environment
        self.token = self.config.get("token") or os.environ.get("GITHUB_TOKEN")

        if not self.token:
            raise RepositoryError(
                "GitHub token not provided. set GITHUB_TOKEN environment variable "
                "or pass token in config."
            )

        self._repo_path: Path | None = None
        self.logger.debug("GitHub repository provider initialized")

    async def get_repository(self, repo_identifier: str) -> dict[str, Any]:
        """Get repository data by identifier.

        Args:
            repo_identifier: Repository identifier (e.g., "username/repo")

        Returns:
            Repository data dictionary

        Raises:
            RepositoryError: If repository cannot be accessed
        """
        raise NotImplementedError("get_repository not implemented")

    async def list_repository_files(
        self, repo_identifier: str, path: str | None = None
    ) -> list[dict[str, Any]]:
        """Get file list from repository.

        Args:
            repo_identifier: Repository identifier
            path: Optional path within repository

        Returns:
            list of file metadata dictionaries

        Raises:
            RepositoryError: If files cannot be accessed
        """
        raise NotImplementedError("list_repository_files not implemented")

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
        raise NotImplementedError("read_repository_file not implemented")

    async def get_commits(
        self, repo_identifier: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get commit history for repository.

        Args:
            repo_identifier: Repository identifier
            limit: Optional limit on number of commits to retrieve

        Returns:
            list of commit metadata dictionaries

        Raises:
            RepositoryError: If commits cannot be accessed
        """
        raise NotImplementedError("get_commits not implemented")

    async def clone(self, url: str, branch: str | None = None) -> str:
        """Clone a repository.

        Args:
            url: Repository URL
            branch: Optional branch to clone

        Returns:
            Path to cloned repository

        Raises:
            RepositoryError: If cloning fails
        """
        # Create temp directory for repo
        repo_dir = tempfile.mkdtemp()
        self._repo_path = Path(repo_dir)

        try:
            # Add token to URL for private repos if token is provided
            if self.token:
                url = url.replace("https://", f"https://{self.token}@")

            # Clone repo
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])
            cmd.extend([url, repo_dir])

            self.logger.debug(f"Cloning repository: {url} to {repo_dir}")

            # Run the command and capture output
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            self.logger.debug(f"Clone successful: {result.stdout}")
            return repo_dir

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to clone repository: {e.stderr}")
            raise RepositoryError(f"Failed to clone repository: {e.stderr}")

    async def get_files(self, path: str | None = None) -> list[str]:
        """Get list of files in repository.

        Args:
            path: Optional path to list files from

        Returns:
            list of file paths

        Raises:
            RepositoryError: If repository not cloned
        """
        if not self._repo_path:
            raise RepositoryError("Repository not cloned")

        base_path = self._repo_path
        if path:
            base_path = base_path / path

        files = []
        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                # Skip .git directory
                rel_path = file_path.relative_to(self._repo_path)
                if not str(rel_path).startswith(".git/"):
                    files.append(str(rel_path))

        return files

    async def get_file_content(self, path: str) -> str:
        """Get content of a file.

        Args:
            path: Path to file

        Returns:
            File content as string

        Raises:
            RepositoryError: If repository not cloned or file not found
        """
        if not self._repo_path:
            raise RepositoryError("Repository not cloned")

        file_path = self._repo_path / path
        if not file_path.exists():
            raise RepositoryError(f"File not found: {path}")

        try:
            return file_path.read_text()
        except Exception as e:
            raise RepositoryError(f"Failed to read file: {e}")

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        if self._repo_path and self._repo_path.exists():
            try:
                # Remove temp directory
                self.logger.debug(
                    f"Cleaning up repository directory: {self._repo_path}"
                )
                subprocess.run(
                    ["rm", "-rf", str(self._repo_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except Exception as e:
                raise ToolError(f"Operation failed: {e}") from e
                self.logger.warning(f"Error cleaning up repository: {e}")

        # Call parent cleanup
        await super().cleanup()
