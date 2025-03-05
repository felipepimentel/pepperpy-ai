"""File handling utilities.

Implements helper functions for file operations and management.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Union


class FileUtils:
    """Utility functions for file manipulation."""

    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """Ensure directory exists.

        Args:
            path: Directory path

        Returns:
            Path object for directory

        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def list_files(
        path: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False,
    ) -> List[Path]:
        """List files in directory.

        Args:
            path: Directory path
            pattern: File pattern
            recursive: Whether to search recursively

        Returns:
            List of file paths

        """
        path = Path(path)
        if recursive:
            return list(path.rglob(pattern))
        return list(path.glob(pattern))

    @staticmethod
    def copy_file(
        src: Union[str, Path],
        dst: Union[str, Path],
        overwrite: bool = False,
    ) -> Path:
        """Copy file.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite existing file

        Returns:
            Path object for destination

        """
        src = Path(src)
        dst = Path(dst)

        if dst.exists() and not overwrite:
            raise FileExistsError(f"File {dst} already exists")

        FileUtils.ensure_dir(dst.parent)
        return Path(shutil.copy2(src, dst))

    @staticmethod
    def move_file(
        src: Union[str, Path],
        dst: Union[str, Path],
        overwrite: bool = False,
    ) -> Path:
        """Move file.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite existing file

        Returns:
            Path object for destination

        """
        src = Path(src)
        dst = Path(dst)

        if dst.exists() and not overwrite:
            raise FileExistsError(f"File {dst} already exists")

        FileUtils.ensure_dir(dst.parent)
        return Path(shutil.move(src, dst))

    @staticmethod
    def delete_file(path: Union[str, Path]) -> None:
        """Delete file.

        Args:
            path: File path

        """
        path = Path(path)
        if path.exists():
            path.unlink()

    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes

        """
        return Path(path).stat().st_size

    @staticmethod
    def get_file_modified_time(path: Union[str, Path]) -> float:
        """Get file modification time.

        Args:
            path: File path

        Returns:
            Modification time as timestamp

        """
        return Path(path).stat().st_mtime

    @staticmethod
    def read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text file.

        Args:
            path: File path
            encoding: File encoding

        Returns:
            File contents as string

        """
        return Path(path).read_text(encoding=encoding)

    @staticmethod
    def write_text(
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Write text file.

        Args:
            path: File path
            content: File contents
            encoding: File encoding

        """
        FileUtils.ensure_dir(Path(path).parent)
        Path(path).write_text(content, encoding=encoding)

    @staticmethod
    def read_bytes(path: Union[str, Path]) -> bytes:
        """Read binary file.

        Args:
            path: File path

        Returns:
            File contents as bytes

        """
        return Path(path).read_bytes()

    @staticmethod
    def write_bytes(path: Union[str, Path], content: bytes) -> None:
        """Write binary file.

        Args:
            path: File path
            content: File contents

        """
        FileUtils.ensure_dir(Path(path).parent)
        Path(path).write_bytes(content)


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists.

    This is a convenience wrapper around FileUtils.ensure_dir.

    Args:
        path: Directory path

    Returns:
        Path object for directory

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     path = ensure_dir(f"{tmp}/test/nested")
        ...     path.exists()
        True
    """
    return FileUtils.ensure_dir(path)


def read_file(
    path: Union[str, Path], encoding: Optional[str] = "utf-8"
) -> Union[str, bytes]:
    """Read file contents.

    This is a convenience wrapper around FileUtils.read_text and FileUtils.read_bytes.

    Args:
        path: File path
        encoding: File encoding (None for binary mode)

    Returns:
        File contents as string or bytes

    Examples:
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        ...     f.write("test content")
        ...     path = f.name
        >>> read_file(path)
        'test content'
        >>> read_file(path, encoding=None)  # Binary mode
        b'test content'
    """
    if encoding is None:
        return FileUtils.read_bytes(path)
    return FileUtils.read_text(path, encoding=encoding)


def write_file(
    path: Union[str, Path],
    content: Union[str, bytes],
    encoding: Optional[str] = "utf-8",
) -> None:
    """Write file contents.

    This is a convenience wrapper around FileUtils.write_text and FileUtils.write_bytes.

    Args:
        path: File path
        content: File contents
        encoding: File encoding (None for binary mode)

    Examples:
        >>> import tempfile, os
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     file_path = f"{tmp}/test.txt"
        ...     write_file(file_path, "test content")
        ...     os.path.exists(file_path)
        True
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     file_path = f"{tmp}/test.bin"
        ...     write_file(file_path, b"binary content", encoding=None)
        ...     os.path.exists(file_path)
        True
    """
    if encoding is None and isinstance(content, bytes):
        FileUtils.write_bytes(path, content)
    elif isinstance(content, str):
        FileUtils.write_text(path, content, encoding=encoding or "utf-8")
    else:
        raise TypeError(
            f"Cannot write content of type {type(content)} with encoding {encoding}"
        )
