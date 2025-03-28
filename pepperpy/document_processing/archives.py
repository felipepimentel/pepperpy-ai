"""Archive handling for document processing.

This module provides functionality for handling archive files (ZIP, RAR, etc.)
in the document processing pipeline.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, List, Optional, Set, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)

# Try to import archive handling libraries
try:
    import zipfile

    ZIPFILE_AVAILABLE = True
except ImportError:
    ZIPFILE_AVAILABLE = False

try:
    import tarfile

    TARFILE_AVAILABLE = True
except ImportError:
    TARFILE_AVAILABLE = False

try:
    import py7zr

    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False

try:
    import rarfile

    RARFILE_AVAILABLE = True
except ImportError:
    RARFILE_AVAILABLE = False


class ArchiveError(PepperpyError):
    """Error raised during archive operations."""

    pass


class ArchiveHandler:
    """Handler for archive files.

    This class provides functionality for extracting files from various
    archive formats (ZIP, RAR, TAR, 7Z, etc.) for document processing.
    """

    # Supported archive extensions and their handler type
    SUPPORTED_EXTENSIONS = {
        ".zip": "zip",
        ".rar": "rar",
        ".tar": "tar",
        ".tar.gz": "tar",
        ".tgz": "tar",
        ".tar.bz2": "tar",
        ".tbz2": "tar",
        ".tar.xz": "tar",
        ".txz": "tar",
        ".7z": "7z",
    }

    # Supported document extensions to extract from archives
    DEFAULT_DOCUMENT_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".md",
        ".markdown",
        ".html",
        ".htm",
        ".docx",
        ".doc",
        ".rtf",
        ".odt",
        ".csv",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
    }

    def __init__(
        self,
        temp_dir: Optional[Union[str, Path]] = None,
        document_extensions: Optional[Set[str]] = None,
        max_size: Optional[int] = None,
        max_files: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize archive handler.

        Args:
            temp_dir: Temporary directory for extracted files
            document_extensions: Set of file extensions to extract
            max_size: Maximum size of archive to process (in bytes)
            max_files: Maximum number of files to extract
            **kwargs: Additional configuration options
        """
        # Set temporary directory
        if temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "pepperpy" / "archives"
        elif isinstance(temp_dir, str):
            self.temp_dir = Path(temp_dir)
        else:
            self.temp_dir = temp_dir

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Set document extensions
        self.document_extensions = (
            document_extensions or self.DEFAULT_DOCUMENT_EXTENSIONS
        )

        # Set size and file limits
        self.max_size = max_size or 100 * 1024 * 1024  # 100 MB default
        self.max_files = max_files or 1000  # 1000 files default

        # Check available archive handlers
        self._check_handlers()

    def _check_handlers(self) -> None:
        """Check which archive handlers are available."""
        self.available_handlers = {
            "zip": ZIPFILE_AVAILABLE,
            "tar": TARFILE_AVAILABLE,
            "7z": PY7ZR_AVAILABLE,
            "rar": RARFILE_AVAILABLE,
        }

        # Log available handlers
        for handler, available in self.available_handlers.items():
            status = "available" if available else "not available"
            logger.debug(f"Archive handler for {handler} is {status}")

    def is_archive(self, file_path: Union[str, Path]) -> bool:
        """Check if a file is a supported archive.

        Args:
            file_path: Path to file

        Returns:
            True if file is a supported archive
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            return False

        # Check file extension
        extension = file_path.suffix.lower()

        # Special case for .tar.* extensions
        if extension in {".gz", ".bz2", ".xz"} and str(file_path).lower().endswith(
            ".tar" + extension
        ):
            return True

        return extension in self.SUPPORTED_EXTENSIONS

    def get_handler_type(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get the handler type for an archive file.

        Args:
            file_path: Path to archive file

        Returns:
            Handler type or None if not a supported archive
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check file extension
        extension = file_path.suffix.lower()
        file_str = str(file_path).lower()

        # Special case for .tar.* extensions
        for ext in [".tar.gz", ".tar.bz2", ".tar.xz"]:
            if file_str.endswith(ext):
                return self.SUPPORTED_EXTENSIONS.get(ext.replace(".tar", ""))

        return self.SUPPORTED_EXTENSIONS.get(extension)

    def list_files(self, archive_path: Union[str, Path]) -> List[str]:
        """List files in an archive.

        Args:
            archive_path: Path to archive file

        Returns:
            List of file paths in the archive

        Raises:
            ArchiveError: If archive cannot be read
        """
        if isinstance(archive_path, str):
            archive_path = Path(archive_path)

        # Check if file exists
        if not archive_path.exists():
            raise ArchiveError(f"Archive file not found: {archive_path}")

        # Check file size
        if archive_path.stat().st_size > self.max_size:
            raise ArchiveError(
                f"Archive file exceeds maximum size ({self.max_size} bytes): {archive_path}"
            )

        # Get handler type
        handler_type = self.get_handler_type(archive_path)
        if not handler_type:
            raise ArchiveError(f"Unsupported archive format: {archive_path}")

        # Check if handler is available
        if not self.available_handlers.get(handler_type, False):
            raise ArchiveError(f"Archive handler for {handler_type} is not available")

        # List files based on handler type
        try:
            if handler_type == "zip":
                return self._list_zip_files(archive_path)
            elif handler_type == "tar":
                return self._list_tar_files(archive_path)
            elif handler_type == "7z":
                return self._list_7z_files(archive_path)
            elif handler_type == "rar":
                return self._list_rar_files(archive_path)
            else:
                raise ArchiveError(f"Unsupported archive format: {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Error listing files in archive: {e}")

    def _list_zip_files(self, archive_path: Path) -> List[str]:
        """List files in a ZIP archive."""
        with zipfile.ZipFile(archive_path) as zip_file:
            return [info.filename for info in zip_file.infolist() if not info.is_dir()]

    def _list_tar_files(self, archive_path: Path) -> List[str]:
        """List files in a TAR archive."""
        with tarfile.open(archive_path) as tar_file:
            return [member.name for member in tar_file.getmembers() if member.isfile()]

    def _list_7z_files(self, archive_path: Path) -> List[str]:
        """List files in a 7Z archive."""
        with py7zr.SevenZipFile(archive_path) as sz_file:
            return [name for name in sz_file.getnames() if not name.endswith("/")]

    def _list_rar_files(self, archive_path: Path) -> List[str]:
        """List files in a RAR archive."""
        with rarfile.RarFile(archive_path) as rar_file:
            return [info.filename for info in rar_file.infolist() if not info.is_dir()]

    def extract_files(
        self,
        archive_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        file_patterns: Optional[List[str]] = None,
    ) -> List[Path]:
        """Extract files from an archive.

        Args:
            archive_path: Path to archive file
            output_dir: Directory to extract files to (defaults to temp dir)
            file_patterns: Patterns of files to extract (defaults to all document files)

        Returns:
            List of paths to extracted files

        Raises:
            ArchiveError: If archive cannot be extracted
        """
        if isinstance(archive_path, str):
            archive_path = Path(archive_path)

        # Check if file exists
        if not archive_path.exists():
            raise ArchiveError(f"Archive file not found: {archive_path}")

        # Check file size
        if archive_path.stat().st_size > self.max_size:
            raise ArchiveError(
                f"Archive file exceeds maximum size ({self.max_size} bytes): {archive_path}"
            )

        # Get handler type
        handler_type = self.get_handler_type(archive_path)
        if not handler_type:
            raise ArchiveError(f"Unsupported archive format: {archive_path}")

        # Check if handler is available
        if not self.available_handlers.get(handler_type, False):
            raise ArchiveError(f"Archive handler for {handler_type} is not available")

        # Set output directory
        if output_dir is None:
            # Create unique temp dir for this archive
            output_dir = self.temp_dir / f"{archive_path.stem}_{os.urandom(4).hex()}"
        elif isinstance(output_dir, str):
            output_dir = Path(output_dir)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract files based on handler type
        try:
            if handler_type == "zip":
                return self._extract_zip_files(archive_path, output_dir, file_patterns)
            elif handler_type == "tar":
                return self._extract_tar_files(archive_path, output_dir, file_patterns)
            elif handler_type == "7z":
                return self._extract_7z_files(archive_path, output_dir, file_patterns)
            elif handler_type == "rar":
                return self._extract_rar_files(archive_path, output_dir, file_patterns)
            else:
                raise ArchiveError(f"Unsupported archive format: {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Error extracting files from archive: {e}")

    def _should_extract_file(
        self, filename: str, file_patterns: Optional[List[str]]
    ) -> bool:
        """Check if a file should be extracted."""
        # If file patterns are specified, check against them
        if file_patterns:
            from fnmatch import fnmatch

            return any(fnmatch(filename, pattern) for pattern in file_patterns)

        # Otherwise, check file extension
        ext = Path(filename).suffix.lower()
        return ext in self.document_extensions

    def _extract_zip_files(
        self, archive_path: Path, output_dir: Path, file_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Extract files from a ZIP archive."""
        extracted_files = []
        with zipfile.ZipFile(archive_path) as zip_file:
            # Get list of files to extract
            files_to_extract = []
            for info in zip_file.infolist():
                if info.is_dir():
                    continue

                if self._should_extract_file(info.filename, file_patterns):
                    files_to_extract.append(info)

                # Check file limit
                if len(files_to_extract) > self.max_files:
                    logger.warning(
                        f"Too many files to extract from {archive_path}. "
                        f"Limiting to {self.max_files} files."
                    )
                    break

            # Extract files
            for info in files_to_extract:
                # Create output path, ensuring the directory exists
                output_path = output_dir / info.filename
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract file
                with zip_file.open(info) as source, open(output_path, "wb") as target:
                    target.write(source.read())

                extracted_files.append(output_path)

        return extracted_files

    def _extract_tar_files(
        self, archive_path: Path, output_dir: Path, file_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Extract files from a TAR archive."""
        extracted_files = []
        with tarfile.open(archive_path) as tar_file:
            # Get list of files to extract
            files_to_extract = []
            for member in tar_file.getmembers():
                if not member.isfile():
                    continue

                if self._should_extract_file(member.name, file_patterns):
                    files_to_extract.append(member)

                # Check file limit
                if len(files_to_extract) > self.max_files:
                    logger.warning(
                        f"Too many files to extract from {archive_path}. "
                        f"Limiting to {self.max_files} files."
                    )
                    break

            # Extract files
            for member in files_to_extract:
                # Create output path, ensuring the directory exists
                output_path = output_dir / member.name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract file - check that extractfile() is not None
                extracted = tar_file.extractfile(member)
                if extracted is not None:
                    with extracted as source, open(output_path, "wb") as target:
                        target.write(source.read())
                else:
                    logger.warning(f"Could not extract {member.name} from archive")
                    continue

                extracted_files.append(output_path)

        return extracted_files

    def _extract_7z_files(
        self, archive_path: Path, output_dir: Path, file_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Extract files from a 7Z archive."""
        extracted_files = []
        with py7zr.SevenZipFile(archive_path) as sz_file:
            # Get list of files to extract
            files_to_extract = []
            for filename in sz_file.getnames():
                if filename.endswith("/"):  # Directory
                    continue

                if self._should_extract_file(filename, file_patterns):
                    files_to_extract.append(filename)

                # Check file limit
                if len(files_to_extract) > self.max_files:
                    logger.warning(
                        f"Too many files to extract from {archive_path}. "
                        f"Limiting to {self.max_files} files."
                    )
                    break

            # Extract files - py7zr only supports extracting all files at once
            # so we extract everything to a temporary directory and then copy
            # the files we want
            with tempfile.TemporaryDirectory() as temp_dir:
                sz_file.extractall(temp_dir)

                # Copy files we want to extract
                for filename in files_to_extract:
                    source_path = Path(temp_dir) / filename
                    output_path = output_dir / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    with (
                        open(source_path, "rb") as source,
                        open(output_path, "wb") as target,
                    ):
                        target.write(source.read())

                    extracted_files.append(output_path)

        return extracted_files

    def _extract_rar_files(
        self, archive_path: Path, output_dir: Path, file_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Extract files from a RAR archive."""
        extracted_files = []
        with rarfile.RarFile(archive_path) as rar_file:
            # Get list of files to extract
            files_to_extract = []
            for info in rar_file.infolist():
                if info.is_dir():
                    continue

                if self._should_extract_file(info.filename, file_patterns):
                    files_to_extract.append(info)

                # Check file limit
                if len(files_to_extract) > self.max_files:
                    logger.warning(
                        f"Too many files to extract from {archive_path}. "
                        f"Limiting to {self.max_files} files."
                    )
                    break

            # Extract files
            for info in files_to_extract:
                # Create output path, ensuring the directory exists
                output_path = output_dir / info.filename
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract file
                with rar_file.open(info) as source, open(output_path, "wb") as target:
                    target.write(source.read())

                extracted_files.append(output_path)

        return extracted_files

    def clean_temp_files(self) -> int:
        """Clean up temporary files.

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.temp_dir.glob("**/*"):
            if path.is_file():
                try:
                    path.unlink()
                    count += 1
                except OSError:
                    # Ignore errors
                    pass

        # Remove empty directories
        for path in sorted(
            self.temp_dir.glob("**/*"), key=lambda p: str(p), reverse=True
        ):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    # Directory not empty or other error
                    pass

        return count


# Global archive handler instance
_archive_handler: Optional[ArchiveHandler] = None


def get_archive_handler(
    temp_dir: Optional[Union[str, Path]] = None,
    document_extensions: Optional[Set[str]] = None,
    max_size: Optional[int] = None,
    max_files: Optional[int] = None,
    **kwargs: Any,
) -> ArchiveHandler:
    """Get archive handler instance.

    Args:
        temp_dir: Temporary directory for extracted files
        document_extensions: Set of file extensions to extract
        max_size: Maximum size of archive to process (in bytes)
        max_files: Maximum number of files to extract
        **kwargs: Additional configuration options

    Returns:
        Archive handler instance
    """
    global _archive_handler

    if _archive_handler is None:
        _archive_handler = ArchiveHandler(
            temp_dir=temp_dir,
            document_extensions=document_extensions,
            max_size=max_size,
            max_files=max_files,
            **kwargs,
        )

    return _archive_handler
