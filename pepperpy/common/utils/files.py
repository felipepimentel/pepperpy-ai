"""Utilitários para manipulação de arquivos.

Implementa funções auxiliares para manipulação de arquivos e diretórios.
"""

import shutil
from pathlib import Path
from typing import List, Union


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
        path: Union[str, Path], pattern: str = "*", recursive: bool = False
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
        src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False
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
        src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False
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
        path: Union[str, Path], content: str, encoding: str = "utf-8"
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
