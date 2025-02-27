"""Handlers de logging para diferentes destinos

Implementação de handlers para logging que suportam diferentes destinos como
arquivos, streams, e outros mecanismos de output.
"""

"""@file: file.py
@purpose: File log handler implementation
@component: Core/Logging
@created: 2024-02-25
@task: TASK-007-R020
@status: completed
"""

"""File handler for logging.

This module provides a file handler that writes log records to files
with support for rotation and compression.
"""

import asyncio
import gzip
import os

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring.logging.base import LogHandler, LogRecord
from pepperpy.monitoring.logging.formatters.json import JsonFormatter


class FileHandler(LogHandler):
    """File log handler."""

    def __init__(
        self,
        name: str,
        filename: str,
        max_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        compress: bool = True,
        indent: int | None = None,
    ) -> None:
        """Initialize file handler.

        Args:
            name: Handler name
            filename: Log file name
            max_size: Maximum file size in bytes
            backup_count: Number of backup files to keep
            compress: Whether to compress backup files
            indent: Optional JSON indentation
        """
        super().__init__(name)
        self.filename = filename
        self.max_size = max_size
        self.backup_count = backup_count
        self.compress = compress
        self._formatter = JsonFormatter(indent=indent)
        self._file = None
        self._lock = asyncio.Lock()

    async def _initialize_handler(self) -> None:
        """Initialize file handler."""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)

            # Open file
            self._file = open(self.filename, "a", encoding="utf-8")
        except Exception as e:
            raise ValidationError(f"Failed to initialize file handler: {e}")

    async def _cleanup_handler(self) -> None:
        """Clean up file handler."""
        if self._file:
            self._file.close()

    async def _handle_record(self, record: LogRecord) -> None:
        """Handle log record.

        Args:
            record: Log record to handle
        """
        if not self._file:
            return

        try:
            # Format record
            formatted = self._formatter.format(record) + "\n"

            async with self._lock:
                # Check if rotation needed
                if self._should_rotate():
                    await self._rotate()

                # Write record
                self._file.write(formatted)
                self._file.flush()

        except Exception as e:
            raise ValidationError(f"Failed to handle log record: {e}")

    def _should_rotate(self) -> bool:
        """Check if file should be rotated.

        Returns:
            True if file should be rotated
        """
        if not self._file:
            return False

        try:
            return os.path.getsize(self.filename) >= self.max_size
        except OSError:
            return False

    async def _rotate(self) -> None:
        """Rotate log files."""
        if not self._file:
            return

        try:
            # Close current file
            self._file.close()

            # Remove old backups
            for i in range(self.backup_count - 1, -1, -1):
                src = f"{self.filename}.{i}"
                dst = f"{self.filename}.{i + 1}"

                if i == 0:
                    src = self.filename

                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)

                    # Compress backup
                    if self.compress and i > 0:
                        with open(dst, "rb") as f_in:
                            with gzip.open(f"{dst}.gz", "wb") as f_out:
                                f_out.writelines(f_in)
                        os.remove(dst)

            # Open new file
            self._file = open(self.filename, "a", encoding="utf-8")

        except Exception as e:
            raise ValidationError(f"Failed to rotate log files: {e}")


# Export public API
__all__ = ["FileHandler"]
"""Logging handlers package.

This package provides handlers for handling log records in various ways.
"""

from pepperpy.monitoring.logging.handlers.file import FileHandler

# Export public API
__all__ = ["FileHandler"]
"""@file: stream.py
@purpose: Stream log handler implementation
@component: Core/Logging
@created: 2024-02-25
@task: TASK-007-R020
@status: completed
"""
