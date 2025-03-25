"""GitHub API client for PepperPy.

This module provides a simple client for interacting with GitHub's API.
"""

import os
from typing import Any, Dict, List, Optional, cast

import aiohttp

from pepperpy.core import ValidationError


class GitHubClient:
    """GitHub API client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            api_key: GitHub API key. If not provided, will try to get from PEPPERPY_TOOLS__GITHUB_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("PEPPERPY_TOOLS__GITHUB_API_KEY")
        if not self.api_key:
            raise ValidationError(
                "GitHub API key not provided and PEPPERPY_TOOLS__GITHUB_API_KEY not set"
            )

        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the client session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.api_key}",
                    "Accept": "application/vnd.github.v3+json",
                }
            )

    async def close(self) -> None:
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_repository(self, repo_identifier: str) -> Dict[str, Any]:
        """Get repository information.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")

        Returns:
            Repository information
        """
        if not self.session:
            await self.initialize()

        url = f"{self.base_url}/repos/{repo_identifier}"
        session = cast(aiohttp.ClientSession, self.session)
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_files(
        self, repo_identifier: str, path: str = ""
    ) -> List[Dict[str, Any]]:
        """Get list of files in repository.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")
            path: Optional path to list files from

        Returns:
            List of file information
        """
        if not self.session:
            await self.initialize()

        url = f"{self.base_url}/repos/{repo_identifier}/contents/{path}"
        session = cast(aiohttp.ClientSession, self.session)
        async with session.get(url) as response:
            response.raise_for_status()
            contents = await response.json()

            files = []
            for item in contents:
                if item["type"] == "file":
                    files.append(item)
                elif item["type"] == "dir":
                    # Recursively get files from subdirectories
                    subdir_files = await self.get_files(repo_identifier, item["path"])
                    files.extend(subdir_files)

            return files

    async def get_file_content(self, repo_identifier: str, path: str) -> str:
        """Get file content.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")
            path: Path to file

        Returns:
            File content as string
        """
        if not self.session:
            await self.initialize()

        url = f"{self.base_url}/repos/{repo_identifier}/contents/{path}"
        session = cast(aiohttp.ClientSession, self.session)
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()

            if data["encoding"] == "base64":
                import base64

                return base64.b64decode(data["content"]).decode("utf-8")
            else:
                return data["content"]

    async def __aenter__(self) -> "GitHubClient":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.close()
