"""Local filesystem storage provider implementation."""

from pathlib import Path
from typing import List, Optional, Union

from pepperpy.storage.base import StorageError, StorageProvider


class LocalStorageProvider(StorageProvider):
    """Provider implementation for local filesystem storage."""

    def __init__(
        self,
        root_path: Union[str, Path],
        create_if_missing: bool = True,
        permissions: Optional[int] = None,
        **kwargs,
    ):
        """Initialize local storage provider.

        Args:
            root_path: Root path for storage operations
            create_if_missing: Create directories if missing
            permissions: File/directory permissions
            **kwargs: Additional parameters

        Raises:
            StorageError: If initialization fails
        """
        self.root_path = Path(root_path).resolve()
        self.create_if_missing = create_if_missing
        self.permissions = permissions

        try:
            if not self.root_path.exists():
                if self.create_if_missing:
                    self.root_path.mkdir(parents=True, exist_ok=True)
                    if self.permissions is not None:
                        self.root_path.chmod(self.permissions)
                else:
                    raise StorageError(f"Root path does not exist: {self.root_path}")
            elif not self.root_path.is_dir():
                raise StorageError(f"Root path is not a directory: {self.root_path}")
        except Exception as e:
            raise StorageError(f"Failed to initialize local storage: {e}")

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to root path.

        Args:
            path: Path to resolve

        Returns:
            Path: Resolved path

        Raises:
            StorageError: If path resolution fails
        """
        try:
            resolved = (self.root_path / Path(path)).resolve()
            if not str(resolved).startswith(str(self.root_path)):
                raise StorageError(f"Path {path} is outside root path")
            return resolved
        except Exception as e:
            raise StorageError(f"Failed to resolve path: {e}")

    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in local filesystem.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        try:
            target = self._resolve_path(path)
            if not target.parent.exists():
                if self.create_if_missing:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if self.permissions is not None:
                        target.parent.chmod(self.permissions)
                else:
                    raise StorageError(
                        f"Parent directory does not exist: {target.parent}"
                    )

            mode = "wb" if isinstance(data, bytes) else "w"
            with open(target, mode) as f:
                f.write(data)

            if self.permissions is not None:
                target.chmod(self.permissions)

        except Exception as e:
            raise StorageError(f"Failed to store data: {e}")

    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from local filesystem.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        try:
            target = self._resolve_path(path)
            if not target.exists():
                raise StorageError(f"File not found: {target}")
            if not target.is_file():
                raise StorageError(f"Path is not a file: {target}")

            with open(target, "rb") as f:
                return f.read()

        except Exception as e:
            raise StorageError(f"Failed to retrieve data: {e}")

    def delete(self, path: Union[str, Path]) -> bool:
        """Delete file from local filesystem.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        try:
            target = self._resolve_path(path)
            if not target.exists():
                return False
            if not target.is_file():
                raise StorageError(f"Path is not a file: {target}")

            target.unlink()
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}")

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in local filesystem.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        try:
            target = self._resolve_path(path)
            return target.exists() and target.is_file()
        except Exception as e:
            raise StorageError(f"Failed to check path: {e}")

    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in local filesystem.

        Args:
            path: Optional path to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
        """
        try:
            target = self._resolve_path(path) if path else self.root_path
            if not target.exists():
                raise StorageError(f"Path does not exist: {target}")
            if not target.is_dir():
                raise StorageError(f"Path is not a directory: {target}")

            files = []
            for item in target.rglob("*"):
                if item.is_file():
                    files.append(str(item.relative_to(self.root_path)))
            return files

        except Exception as e:
            raise StorageError(f"Failed to list files: {e}")

    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get URL for accessing file in local filesystem.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds (ignored)

        Returns:
            str: URL for accessing file

        Raises:
            StorageError: If URL generation fails
        """
        try:
            target = self._resolve_path(path)
            if not target.exists():
                raise StorageError(f"File not found: {target}")
            if not target.is_file():
                raise StorageError(f"Path is not a file: {target}")

            return f"file://{target}"

        except Exception as e:
            raise StorageError(f"Failed to generate URL: {e}")
