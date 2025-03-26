"""GitHub repository provider for PepperPy.

This module provides an implementation of the repository provider interface
for GitHub repositories.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, cast
from urllib.parse import urlparse

from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository

from pepperpy.core.config import Config
from pepperpy.tools.base import ConnectionError
from pepperpy.tools.repository.base import RepositoryError, RepositoryProvider


class GitHubProvider(RepositoryProvider):
    """GitHub repository provider implementation."""

    def __init__(self, config: Config) -> None:
        """Initialize GitHub provider.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._client: Optional[Github] = None
        self._repo: Optional[Repository] = None
        self.logger = logging.getLogger("pepperpy.tools.repository.github")
        self._connected = False

    async def initialize(self) -> None:
        """Initialize the GitHub client."""
        token = self.config.get("github.token")
        if not token:
            token = self.config.get("tools.github_api_key")
        if not token:
            raise ValueError(
                "GitHub token not found. Set PEPPERPY_TOOLS__GITHUB_API_KEY "
                "environment variable."
            )
        self._client = Github(token)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            self._client.close()
            self._client = None
            self._repo = None

    def capabilities(self) -> Set[str]:
        """Return the capabilities supported by this provider.

        Returns:
            Set of capability strings
        """
        return {
            "github_repositories",
            "public_repositories",
            "private_repositories",
            "file_access",
            "commit_history",
        }

    async def connect(self) -> bool:
        """Connect to GitHub API.

        Returns:
            True if successfully connected, False otherwise

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        self.logger.info("Connecting to GitHub API")
        try:
            await asyncio.sleep(0.1)  # Simulate API call
            self._connected = True
            return True
        except Exception as e:
            error_msg = f"Failed to connect to GitHub API: {e}"
            self.logger.error(error_msg)

            # For this example, we'll just raise a generic error
            raise ConnectionError(error_msg)

    async def disconnect(self) -> bool:
        """Disconnect from GitHub API.

        Returns:
            True if successfully disconnected, False otherwise
        """
        self.logger.info("Disconnecting from GitHub API")
        # GitHub API client doesn't require explicit disconnection
        # but we'll reset our state
        self._client = None
        self._connected = False
        return True

    async def test_connection(self) -> bool:
        """Test the connection to GitHub API.

        Returns:
            True if connection is working, False otherwise
        """
        if not self._connected:
            try:
                return await self.connect()
            except Exception:
                return False

        try:
            await asyncio.sleep(0.1)  # Simulate API call
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def get_repository(self, url: str) -> Repository:
        """Get repository by URL.

        Args:
            url: Repository URL

        Returns:
            Repository instance

        Raises:
            ValueError: If GitHub client initialization fails
        """
        if not self._client:
            await self.initialize()
            if not self._client:
                raise ValueError("Failed to initialize GitHub client")

        # Extract owner and repo name from URL
        parts = url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]

        # Get repository
        repo = self._client.get_repo(f"{owner}/{repo}")
        if not repo:
            raise ValueError(f"Repository not found: {owner}/{repo}")

        self._repo = repo
        return repo

    async def get_file_contents(self, path: str) -> str:
        """Get file contents.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            ValueError: If repository not initialized
        """
        if not self._repo:
            raise ValueError("Repository not initialized")

        contents = self._repo.get_contents(path)
        if isinstance(contents, list):
            raise ValueError(f"Path {path} is a directory")

        return cast(ContentFile, contents).decoded_content.decode("utf-8")

    async def get_files(self, path: str = "") -> List[str]:
        """Get list of files in repository.

        Args:
            path: Optional path to list files from

        Returns:
            List of file paths

        Raises:
            ValueError: If repository not initialized
        """
        if not self._repo:
            raise ValueError("Repository not initialized")

        files = []
        contents = self._repo.get_contents(path)
        if not isinstance(contents, list):
            contents = [contents]

        while contents:
            file_content = cast(ContentFile, contents.pop(0))
            if file_content.type == "dir":
                dir_contents = self._repo.get_contents(file_content.path)
                if isinstance(dir_contents, list):
                    contents.extend(dir_contents)
                else:
                    contents.append(dir_contents)
            else:
                files.append(file_content.path)

        return files

    async def get_repository_data(self, repo_identifier: str) -> Dict[str, Any]:
        """Get repository data by identifier.

        Args:
            repo_identifier: Repository identifier in format "username/repo" or GitHub URL

        Returns:
            Repository data dictionary

        Raises:
            RepositoryError: If repository cannot be accessed
        """
        if not self._connected:
            await self.connect()

        try:
            self.logger.info(f"Getting repository data for {repo_identifier}")

            # Parse GitHub URL if provided
            if repo_identifier.startswith("http"):
                parsed = urlparse(repo_identifier)
                if parsed.netloc != "github.com":
                    raise RepositoryError(f"Not a GitHub URL: {repo_identifier}")
                repo_identifier = parsed.path.strip("/")

            # In a real implementation, you would retrieve the repository from GitHub
            # username, repo_name = repo_identifier.split('/')
            # github_repo = self._client.get_repo(repo_identifier)
            # data = self._convert_github_repo_to_dict(github_repo)

            # For this example, we'll just create mock data
            owner, name = repo_identifier.split("/")
            await asyncio.sleep(0.2)  # Simulate API call

            # Mock repository data
            return {
                "repository": {
                    "name": name,
                    "url": f"https://github.com/{repo_identifier}",
                    "description": "Mock repository data",
                    "languages": {
                        "Python": 65.5,
                        "JavaScript": 25.3,
                        "HTML": 6.2,
                        "CSS": 3.0,
                    },
                    "files_count": 156,
                    "directories": {
                        "src": {"count": 45, "type": "source"},
                        "tests": {"count": 32, "type": "test"},
                        "docs": {"count": 12, "type": "documentation"},
                    },
                    "entry_points": ["main.py", "app.py"],
                    "test_directories": ["tests/", "src/*/tests/"],
                },
                "code_quality": {
                    "maintainability_index": 78.5,
                    "cyclomatic_complexity": 12.3,
                    "code_duplication": 7.8,
                    "test_coverage": 85.2,
                    "documentation_coverage": 62.7,
                    "issues": {
                        "critical": [
                            {
                                "file": "src/auth.py",
                                "line": 45,
                                "message": "Insecure token generation",
                            }
                        ],
                        "major": [
                            {
                                "file": "src/database.py",
                                "line": 128,
                                "message": "Unhandled SQL injection risk",
                            },
                            {
                                "file": "src/api/users.py",
                                "line": 89,
                                "message": "Unprotected endpoint",
                            },
                        ],
                        "minor": [
                            {
                                "file": "src/utils.py",
                                "line": 210,
                                "message": "Unused import",
                            },
                            {
                                "file": "src/models/product.py",
                                "line": 35,
                                "message": "Duplicate code",
                            },
                        ],
                    },
                },
                "security": {
                    "alerts": [
                        {
                            "level": "high",
                            "component": "auth",
                            "description": "Insecure token generation",
                            "cve": "CVE-2023-1234",
                        },
                        {
                            "level": "medium",
                            "component": "database",
                            "description": "SQL injection vulnerability",
                            "cve": None,
                        },
                    ]
                },
            }
        except Exception as e:
            error_msg = f"Failed to get repository {repo_identifier}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg)

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
        if not self._connected:
            await self.connect()

        try:
            self.logger.info(f"Getting content of {file_path} in {repo_identifier}")

            # In a real implementation, you would retrieve file content from GitHub
            # github_repo = self._client.get_repo(repo_identifier)
            # content = github_repo.get_contents(file_path)
            # return content.decoded_content.decode('utf-8')

            # For this example, we'll just create mock content
            await asyncio.sleep(0.2)  # Simulate API call

            # Mock file content based on file extension
            if file_path.endswith(".py"):
                return 'def main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()'
            elif file_path.endswith(".md"):
                return "# Project Title\n\nThis is a sample project.\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```"
            elif file_path.endswith(".txt"):
                return "numpy==1.21.0\npandas==1.3.0\nrequests==2.26.0"
            else:
                return f"Content of {file_path}"
        except Exception as e:
            error_msg = (
                f"Failed to get content of {file_path} in {repo_identifier}: {e}"
            )
            self.logger.error(error_msg)
            raise RepositoryError(error_msg)

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
        if not self._connected:
            await self.connect()

        try:
            self.logger.info(f"Getting commits for {repo_identifier}")

            # In a real implementation, you would retrieve commits from GitHub
            # github_repo = self._client.get_repo(repo_identifier)
            # commits = github_repo.get_commits()
            # result = []
            # count = 0
            # for commit in commits:
            #     result.append(self._convert_commit_to_dict(commit))
            #     count += 1
            #     if limit and count >= limit:
            #         break
            # return result

            # For this example, we'll just create mock data
            await asyncio.sleep(0.2)  # Simulate API call

            # Mock commit history
            result_limit = limit or 3  # Default to 3 commits if no limit specified
            return [
                {
                    "sha": f"abc123{i}",
                    "author": "johndoe",
                    "date": "2023-06-0{i}T10:00:00Z",
                    "message": f"Commit message {i}",
                }
                for i in range(1, result_limit + 1)
            ]
        except Exception as e:
            error_msg = f"Failed to get commits for {repo_identifier}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg)
