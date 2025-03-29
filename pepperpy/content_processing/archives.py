"""Archive handling module.

This module provides functionality for handling archive files.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.core.base import PepperpyError
from pepperpy.content_processing.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class ArchiveError(PepperpyError):
    """Error raised when handling archives."""

    pass


class ArchiveHandler:
    """Handler for archive files."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize archive handler.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs
        self._temp_dir = None

    async def extract_archive(
        self,
        archive_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract archive contents.

        Args:
            archive_path: Path to archive file
            output_path: Path to extract contents (optional)
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with extraction results

        Raises:
            ArchiveError: If extraction fails
        """
        if isinstance(archive_path, str):
            archive_path = Path(archive_path)

        if not archive_path.exists():
            raise ArchiveError(f"Archive not found: {archive_path}")

        try:
            # Set output path if not provided
            if output_path is None:
                output_path = archive_path.parent / archive_path.stem
            elif isinstance(output_path, str):
                output_path = Path(output_path)

            # Get file extension
            extension = archive_path.suffix.lower()

            # Extract based on file type
            if extension == ".zip":
                return await self._extract_zip(
                    archive_path, output_path, password, **kwargs
                )
            elif extension == ".rar":
                return await self._extract_rar(
                    archive_path, output_path, password, **kwargs
                )
            elif extension == ".7z":
                return await self._extract_7z(
                    archive_path, output_path, password, **kwargs
                )
            elif extension in (".tar", ".gz", ".bz2", ".xz"):
                return await self._extract_tar(
                    archive_path, output_path, **kwargs
                )
            else:
                raise ArchiveError(f"Unsupported archive type: {extension}")

        except Exception as e:
            raise ArchiveError(f"Error extracting archive: {e}")

    async def create_archive(
        self,
        source_path: Union[str, Path],
        archive_path: Optional[Union[str, Path]] = None,
        archive_type: str = "zip",
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create archive from files.

        Args:
            source_path: Path to source file or directory
            archive_path: Path to save archive (optional)
            archive_type: Type of archive to create
            password: Password to protect archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive creation results

        Raises:
            ArchiveError: If archive creation fails
        """
        if isinstance(source_path, str):
            source_path = Path(source_path)

        if not source_path.exists():
            raise ArchiveError(f"Source not found: {source_path}")

        try:
            # Set archive path if not provided
            if archive_path is None:
                archive_path = source_path.parent / f"{source_path.name}.{archive_type}"
            elif isinstance(archive_path, str):
                archive_path = Path(archive_path)

            # Create archive based on type
            if archive_type == "zip":
                return await self._create_zip(
                    source_path, archive_path, password, **kwargs
                )
            elif archive_type == "rar":
                return await self._create_rar(
                    source_path, archive_path, password, **kwargs
                )
            elif archive_type == "7z":
                return await self._create_7z(
                    source_path, archive_path, password, **kwargs
                )
            elif archive_type in ("tar", "gz", "bz2", "xz"):
                return await self._create_tar(
                    source_path, archive_path, archive_type, **kwargs
                )
            else:
                raise ArchiveError(f"Unsupported archive type: {archive_type}")

        except Exception as e:
            raise ArchiveError(f"Error creating archive: {e}")

    async def list_contents(
        self,
        archive_path: Union[str, Path],
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List archive contents.

        Args:
            archive_path: Path to archive file
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive contents

        Raises:
            ArchiveError: If listing fails
        """
        if isinstance(archive_path, str):
            archive_path = Path(archive_path)

        if not archive_path.exists():
            raise ArchiveError(f"Archive not found: {archive_path}")

        try:
            # Get file extension
            extension = archive_path.suffix.lower()

            # List contents based on file type
            if extension == ".zip":
                return await self._list_zip(archive_path, password, **kwargs)
            elif extension == ".rar":
                return await self._list_rar(archive_path, password, **kwargs)
            elif extension == ".7z":
                return await self._list_7z(archive_path, password, **kwargs)
            elif extension in (".tar", ".gz", ".bz2", ".xz"):
                return await self._list_tar(archive_path, **kwargs)
            else:
                raise ArchiveError(f"Unsupported archive type: {extension}")

        except Exception as e:
            raise ArchiveError(f"Error listing archive contents: {e}")

    async def _extract_zip(
        self,
        archive_path: Path,
        output_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract ZIP archive.

        Args:
            archive_path: Path to ZIP file
            output_path: Path to extract contents
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with extraction results
        """
        try:
            import zipfile

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Extract ZIP
            with zipfile.ZipFile(archive_path) as zip_file:
                # Check if password is needed
                if any(info.flag_bits & 0x1 for info in zip_file.filelist):
                    if not password:
                        raise ArchiveError("Password required for ZIP archive")
                    pwd = password.encode()
                else:
                    pwd = None

                # Extract files
                zip_file.extractall(path=output_path, pwd=pwd)

            return {
                "success": True,
                "output_path": str(output_path),
                "num_files": len(zip_file.filelist),
            }

        except ImportError:
            raise ArchiveError("zipfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error extracting ZIP archive: {e}")

    async def _extract_rar(
        self,
        archive_path: Path,
        output_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract RAR archive.

        Args:
            archive_path: Path to RAR file
            output_path: Path to extract contents
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with extraction results
        """
        try:
            import rarfile

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Extract RAR
            with rarfile.RarFile(archive_path) as rar_file:
                # Check if password is needed
                if rar_file.needs_password():
                    if not password:
                        raise ArchiveError("Password required for RAR archive")

                # Extract files
                rar_file.extractall(path=output_path, pwd=password)

            return {
                "success": True,
                "output_path": str(output_path),
                "num_files": len(rar_file.filelist),
            }

        except ImportError:
            raise ArchiveError("rarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error extracting RAR archive: {e}")

    async def _extract_7z(
        self,
        archive_path: Path,
        output_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract 7Z archive.

        Args:
            archive_path: Path to 7Z file
            output_path: Path to extract contents
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with extraction results
        """
        try:
            import py7zr

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Extract 7Z
            with py7zr.SevenZipFile(
                archive_path,
                mode="r",
                password=password,
            ) as z7_file:
                # Check if password is needed
                if z7_file.needs_password():
                    if not password:
                        raise ArchiveError("Password required for 7Z archive")

                # Extract files
                z7_file.extractall(path=output_path)

            return {
                "success": True,
                "output_path": str(output_path),
                "num_files": len(z7_file.files),
            }

        except ImportError:
            raise ArchiveError("py7zr module not available")
        except Exception as e:
            raise ArchiveError(f"Error extracting 7Z archive: {e}")

    async def _extract_tar(
        self,
        archive_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract TAR archive.

        Args:
            archive_path: Path to TAR file
            output_path: Path to extract contents
            **kwargs: Additional options

        Returns:
            Dictionary with extraction results
        """
        try:
            import tarfile

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Extract TAR
            with tarfile.open(archive_path) as tar_file:
                # Extract files
                tar_file.extractall(path=output_path)

            return {
                "success": True,
                "output_path": str(output_path),
                "num_files": len(tar_file.getmembers()),
            }

        except ImportError:
            raise ArchiveError("tarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error extracting TAR archive: {e}")

    async def _create_zip(
        self,
        source_path: Path,
        archive_path: Path,
        password: Optional[str] = None,
        compression: int = 8,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create ZIP archive.

        Args:
            source_path: Path to source file or directory
            archive_path: Path to save archive
            password: Password to protect archive (optional)
            compression: Compression level (0-9)
            **kwargs: Additional options

        Returns:
            Dictionary with archive creation results
        """
        try:
            import zipfile

            # Create ZIP
            with zipfile.ZipFile(
                archive_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=compression,
            ) as zip_file:
                # Add files
                if source_path.is_file():
                    # Add single file
                    zip_file.write(
                        source_path,
                        arcname=source_path.name,
                    )
                else:
                    # Add directory contents
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            zip_file.write(
                                file_path,
                                arcname=str(file_path.relative_to(source_path)),
                            )

            return {
                "success": True,
                "archive_path": str(archive_path),
                "num_files": len(zip_file.filelist),
            }

        except ImportError:
            raise ArchiveError("zipfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error creating ZIP archive: {e}")

    async def _create_rar(
        self,
        source_path: Path,
        archive_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create RAR archive.

        Args:
            source_path: Path to source file or directory
            archive_path: Path to save archive
            password: Password to protect archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive creation results
        """
        try:
            import rarfile

            # Check if RAR executable is available
            if not rarfile.UNRAR_TOOL:
                raise ArchiveError("RAR executable not found")

            # Create RAR
            with rarfile.RarFile(archive_path, mode="w") as rar_file:
                # Add files
                if source_path.is_file():
                    # Add single file
                    rar_file.write(
                        source_path,
                        arcname=source_path.name,
                    )
                else:
                    # Add directory contents
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            rar_file.write(
                                file_path,
                                arcname=str(file_path.relative_to(source_path)),
                            )

            return {
                "success": True,
                "archive_path": str(archive_path),
                "num_files": len(rar_file.filelist),
            }

        except ImportError:
            raise ArchiveError("rarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error creating RAR archive: {e}")

    async def _create_7z(
        self,
        source_path: Path,
        archive_path: Path,
        password: Optional[str] = None,
        compression: int = 6,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create 7Z archive.

        Args:
            source_path: Path to source file or directory
            archive_path: Path to save archive
            password: Password to protect archive (optional)
            compression: Compression level (0-9)
            **kwargs: Additional options

        Returns:
            Dictionary with archive creation results
        """
        try:
            import py7zr

            # Create 7Z
            with py7zr.SevenZipFile(
                archive_path,
                mode="w",
                password=password,
            ) as z7_file:
                # Add files
                if source_path.is_file():
                    # Add single file
                    z7_file.write(source_path, arcname=source_path.name)
                else:
                    # Add directory contents
                    z7_file.writeall(source_path, arcname=".")

            return {
                "success": True,
                "archive_path": str(archive_path),
                "num_files": len(z7_file.files),
            }

        except ImportError:
            raise ArchiveError("py7zr module not available")
        except Exception as e:
            raise ArchiveError(f"Error creating 7Z archive: {e}")

    async def _create_tar(
        self,
        source_path: Path,
        archive_path: Path,
        archive_type: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create TAR archive.

        Args:
            source_path: Path to source file or directory
            archive_path: Path to save archive
            archive_type: Type of TAR archive
            **kwargs: Additional options

        Returns:
            Dictionary with archive creation results
        """
        try:
            import tarfile

            # Set compression mode
            if archive_type == "tar":
                mode = "w"
            elif archive_type == "gz":
                mode = "w:gz"
            elif archive_type == "bz2":
                mode = "w:bz2"
            elif archive_type == "xz":
                mode = "w:xz"
            else:
                raise ArchiveError(f"Unsupported TAR type: {archive_type}")

            # Create TAR
            with tarfile.open(archive_path, mode=mode) as tar_file:
                # Add files
                if source_path.is_file():
                    # Add single file
                    tar_file.add(
                        source_path,
                        arcname=source_path.name,
                    )
                else:
                    # Add directory contents
                    tar_file.add(
                        source_path,
                        arcname=".",
                        recursive=True,
                    )

            return {
                "success": True,
                "archive_path": str(archive_path),
                "num_files": len(tar_file.getmembers()),
            }

        except ImportError:
            raise ArchiveError("tarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error creating TAR archive: {e}")

    async def _list_zip(
        self,
        archive_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List ZIP archive contents.

        Args:
            archive_path: Path to ZIP file
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive contents
        """
        try:
            import zipfile

            # Open ZIP
            with zipfile.ZipFile(archive_path) as zip_file:
                # Check if password is needed
                if any(info.flag_bits & 0x1 for info in zip_file.filelist):
                    if not password:
                        raise ArchiveError("Password required for ZIP archive")

                # Get file list
                files = []
                for info in zip_file.filelist:
                    files.append({
                        "name": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "date_time": info.date_time,
                        "is_dir": info.filename.endswith("/"),
                    })

                return {
                    "success": True,
                    "num_files": len(files),
                    "files": files,
                }

        except ImportError:
            raise ArchiveError("zipfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error listing ZIP archive contents: {e}")

    async def _list_rar(
        self,
        archive_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List RAR archive contents.

        Args:
            archive_path: Path to RAR file
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive contents
        """
        try:
            import rarfile

            # Open RAR
            with rarfile.RarFile(archive_path) as rar_file:
                # Check if password is needed
                if rar_file.needs_password():
                    if not password:
                        raise ArchiveError("Password required for RAR archive")

                # Get file list
                files = []
                for info in rar_file.infolist():
                    files.append({
                        "name": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "date_time": info.date_time,
                        "is_dir": info.is_dir(),
                    })

                return {
                    "success": True,
                    "num_files": len(files),
                    "files": files,
                }

        except ImportError:
            raise ArchiveError("rarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error listing RAR archive contents: {e}")

    async def _list_7z(
        self,
        archive_path: Path,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List 7Z archive contents.

        Args:
            archive_path: Path to 7Z file
            password: Password to unlock archive (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with archive contents
        """
        try:
            import py7zr

            # Open 7Z
            with py7zr.SevenZipFile(
                archive_path,
                mode="r",
                password=password,
            ) as z7_file:
                # Check if password is needed
                if z7_file.needs_password():
                    if not password:
                        raise ArchiveError("Password required for 7Z archive")

                # Get file list
                files = []
                for filename, info in z7_file.files.items():
                    files.append({
                        "name": filename,
                        "size": info.uncompressed,
                        "compressed_size": info.compressed,
                        "date_time": info.creationtime,
                        "is_dir": info.is_directory,
                    })

                return {
                    "success": True,
                    "num_files": len(files),
                    "files": files,
                }

        except ImportError:
            raise ArchiveError("py7zr module not available")
        except Exception as e:
            raise ArchiveError(f"Error listing 7Z archive contents: {e}")

    async def _list_tar(
        self,
        archive_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List TAR archive contents.

        Args:
            archive_path: Path to TAR file
            **kwargs: Additional options

        Returns:
            Dictionary with archive contents
        """
        try:
            import tarfile

            # Open TAR
            with tarfile.open(archive_path) as tar_file:
                # Get file list
                files = []
                for info in tar_file.getmembers():
                    files.append({
                        "name": info.name,
                        "size": info.size,
                        "date_time": info.mtime,
                        "is_dir": info.isdir(),
                    })

                return {
                    "success": True,
                    "num_files": len(files),
                    "files": files,
                }

        except ImportError:
            raise ArchiveError("tarfile module not available")
        except Exception as e:
            raise ArchiveError(f"Error listing TAR archive contents: {e}")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir) 