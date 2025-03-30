import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.base import ValidationError
from pepperpy.tools.repository.base import RepositoryProvider


class GitHubProvider(RepositoryProvider):
    """GitHub repository provider implementation."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        token: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize GitHub repository provider.

        Args:
            token: Optional GitHub access token
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self._repo_path: Optional[Path] = None

    async def initialize(self) -> None:
        """Initialize the repository provider."""
        if not self.token:
            raise ValidationError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable "
                "or pass token in constructor."
            )

    async def get_repository(self, repo_identifier: str) -> Dict[str, Any]:
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
        raise NotImplementedError("get_commits not implemented")

    async def clone(self, url: str, branch: Optional[str] = None) -> str:
        """Clone a repository.

        Args:
            url: Repository URL
            branch: Optional branch to clone

        Returns:
            Path to cloned repository

        Raises:
            ValidationError if cloning fails
        """
        # Create temp directory for repo
        repo_dir = tempfile.mkdtemp()
        self._repo_path = Path(repo_dir)

        try:
            # Add token to URL for private repos
            if self.token:
                url = url.replace("https://", f"https://{self.token}@")

            # Clone repo
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])
            cmd.extend([url, repo_dir])

            subprocess.run(cmd, check=True, capture_output=True, text=True)

            return repo_dir

        except subprocess.CalledProcessError as e:
            raise ValidationError(f"Failed to clone repository: {e.stderr}")

    async def get_files(self, path: Optional[str] = None) -> List[str]:
        """Get list of files in repository.

        Args:
            path: Optional path to list files from

        Returns:
            List of file paths

        Raises:
            ValidationError if repository not cloned
        """
        if not self._repo_path:
            raise ValidationError("Repository not cloned")

        base_path = self._repo_path
        if path:
            base_path = base_path / path

        files = []
        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                files.append(str(file_path.relative_to(self._repo_path)))

        return files

    async def get_file_content(self, path: str) -> str:
        """Get content of a file.

        Args:
            path: Path to file

        Returns:
            File content as string

        Raises:
            ValidationError if repository not cloned or file not found
        """
        if not self._repo_path:
            raise ValidationError("Repository not cloned")

        file_path = self._repo_path / path
        if not file_path.exists():
            raise ValidationError(f"File not found: {path}")

        return file_path.read_text()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._repo_path and self._repo_path.exists():
            # Remove temp directory
            subprocess.run(
                ["rm", "-rf", str(self._repo_path)],
                check=True,
                capture_output=True,
                text=True,
            )
