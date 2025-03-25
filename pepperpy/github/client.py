"""GitHub client module."""

from typing import Dict, List

from github.ContentFile import ContentFile
from github.Repository import Repository
from PyGithub import Github


class GitHubClient:
    """GitHub client class."""

    def __init__(self, api_key: str) -> None:
        """Initialize GitHub client.

        Args:
            api_key: GitHub API key.
        """
        self.client = Github(api_key)

    async def initialize(self) -> None:
        """Initialize the client."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def get_repository(self, repo_url: str) -> Dict[str, str]:
        """Get repository from URL.

        Args:
            repo_url: Repository URL.

        Returns:
            Repository information.
        """
        # Extract owner and repo name from URL
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]
        repo_obj = self.client.get_repo(f"{owner}/{repo}")
        return {
            "name": repo_obj.name,
            "description": repo_obj.description or "",
            "url": repo_obj.html_url,
            "owner": owner,
        }

    async def get_files(self, repo_url: str) -> List[Dict[str, str]]:
        """Get repository files.

        Args:
            repo_url: Repository URL.

        Returns:
            List of files with their paths.
        """
        # Extract owner and repo name from URL
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]
        repo_obj = self.client.get_repo(f"{owner}/{repo}")
        return await self._get_repository_files(repo_obj)

    async def get_file_content(self, repo_url: str, file_path: str) -> str:
        """Get file content.

        Args:
            repo_url: Repository URL.
            file_path: Path to file in repository.

        Returns:
            File content.
        """
        # Extract owner and repo name from URL
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]
        repo_obj = self.client.get_repo(f"{owner}/{repo}")
        content = repo_obj.get_contents(file_path)
        if isinstance(content, ContentFile):
            return content.decoded_content.decode("utf-8")
        raise ValueError(f"File {file_path} not found or is a directory")

    async def _get_repository_files(
        self, repo: Repository, path: str = "", recursive: bool = True
    ) -> List[Dict[str, str]]:
        """Get repository files recursively.

        Args:
            repo: Repository object.
            path: Path to get files from.
            recursive: Whether to get files recursively.

        Returns:
            List of files with their paths.
        """
        files = []
        contents = repo.get_contents(path)
        if not isinstance(contents, list):
            contents = [contents]

        while contents:
            content = contents[0]
            contents = contents[1:]
            if content.type == "dir" and recursive:
                dir_contents = repo.get_contents(content.path)
                if isinstance(dir_contents, list):
                    contents.extend(dir_contents)
                else:
                    contents.append(dir_contents)
            elif content.type == "file":
                files.append({
                    "name": content.name,
                    "path": content.path,
                })
        return files
