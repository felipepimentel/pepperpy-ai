"""
PepperPy Result Objects.

This module provides results handling for the PepperPy framework,
allowing intelligent result objects that can save themselves and include metadata.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pepperpy.core.errors import PepperpyError


class PepperResultError(PepperpyError):
    """Error raised during result operations."""

    pass


class Logger:
    """Centralized logging for PepperPy framework."""

    def __init__(
        self,
        name: str = "pepperpy",
        level: str | int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file: Path | None = None,
        format_string: str | None = None,
    ):
        """Initialize logger with specified configuration.

        Args:
            name: Logger name
            level: Logging level
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            log_file: Optional custom log file path
            format_string: Optional custom format string
        """
        self.logger = logging.getLogger(name)

        # Convert string level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self.logger.setLevel(level)
        self.handlers = []

        # Default format
        if not format_string:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.handlers.append(console_handler)

        # File handler
        if log_to_file:
            if not log_file:
                # Default to logs directory in current working directory
                logs_dir = Path.cwd() / "logs"
                os.makedirs(logs_dir, exist_ok=True)
                log_file = (
                    logs_dir
                    / f"pepperpy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.handlers.append(file_handler)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)

    def header(self, title: str, char: str = "=", width: int = 80) -> None:
        """Log a formatted header.

        Args:
            title: Header title
            char: Character to use for the header line
            width: Width of the header
        """
        self.info(char * width)
        self.info(title.center(width))
        self.info(char * width)

    def section(self, title: str, char: str = "-", width: int = 60) -> None:
        """Log a section header.

        Args:
            title: Section title
            char: Character to use for the section line
            width: Width of the section header
        """
        self.info("\n" + title)
        self.info(char * len(title))

    def cleanup(self) -> None:
        """Clean up logger resources."""
        for handler in self.handlers:
            handler.close()
            self.logger.removeHandler(handler)


class PepperResult:
    """Base class for all PepperPy results.

    This class provides common functionality for all results returned by
    PepperPy operations, including the ability to save results to files.
    """

    def __init__(
        self,
        content: Any,
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a result object.

        Args:
            content: The actual result content
            metadata: Optional metadata about the result
            logger: Optional logger instance
        """
        self.content = content
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.logger = logger or Logger()

    def __str__(self) -> str:
        """String representation of the result."""
        return str(self.content)

    def save(
        self, path: str | Path, header: str | None = None, encoding: str = "utf-8"
    ) -> Path:
        """Save the result to a file.

        Args:
            path: Path to save the result
            header: Optional header to add before the content
            encoding: File encoding

        Returns:
            Path to the saved file

        Raises:
            PepperResultError: If the save operation fails
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            content_str = str(self.content)
            if header:
                content_str = f"{header}\n\n{content_str}"

            with open(path, "w", encoding=encoding) as f:
                f.write(content_str)

            self.logger.info(f"Result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save result: {e!s}", cause=e)


class TextResult:
    """Base class for text-based results."""

    def __init__(self, content: str, metadata: dict[str, Any] | None = None):
        """Initialize text result.

        Args:
            content: Result content
            metadata: Additional metadata
        """
        self.content = content
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation of the result."""
        return self.content

    def save(self, path: Path) -> Path:
        """Save the result to a file.

        Args:
            path: Path to save the result

        Returns:
            Path to the saved file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)
        return path

    def save_with_metadata(self, path: Path) -> Path:
        """Save the result with metadata to a file.

        Args:
            path: Path to save the result

        Returns:
            Path to the saved file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Result\n\n")
            f.write(self.content)
            f.write("\n\n# Metadata\n\n")
            f.write(json.dumps(self.metadata, indent=2))
        return path

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
        }


class JSONResult(PepperResult):
    """Result containing JSON content."""

    def __init__(
        self,
        content: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a JSON result.

        Args:
            content: JSON content as dictionary
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)

    def __str__(self) -> str:
        """Format JSON content as a string."""
        return json.dumps(self.content, indent=2)

    def save(
        self, path: str | Path, header: str | None = None, encoding: str = "utf-8"
    ) -> Path:
        """Save the JSON result to a file.

        Args:
            path: Path to save the result
            header: Optional header as a comment
            encoding: File encoding

        Returns:
            Path to the saved file
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                if header:
                    f.write(f"// {header}\n")
                json.dump(self.content, f, indent=2)

            self.logger.info(f"JSON result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save JSON result: {e!s}", cause=e)


class MemoryResult(PepperResult):
    """Result with conversation memory context."""

    def __init__(
        self,
        content: str,
        conversation_history: list[dict[str, str]],
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a memory result.

        Args:
            content: Result content
            conversation_history: Conversation history
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)
        self.conversation_history = conversation_history

    def save_with_context(
        self,
        path: str | Path,
        conversation_history: list[dict[str, str]] | None = None,
        new_query: str | None = None,
        encoding: str = "utf-8",
    ) -> Path:
        """Save the result with conversation context.

        Args:
            path: Path to save the result
            conversation_history: Optional conversation history (uses instance if None)
            new_query: Optional new query to add to the output
            encoding: File encoding

        Returns:
            Path to the saved file
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            history = conversation_history or self.conversation_history

            with open(path, "w", encoding=encoding) as f:
                f.write("# Conversation History\n\n")

                for msg in history:
                    role = msg["role"]
                    content = msg["content"]
                    f.write(f"**{role.capitalize()}**: {content}\n\n")

                if new_query:
                    f.write(f"**User**: {new_query}\n\n")

                f.write(f"**Assistant**: {self.content}\n")

            self.logger.info(f"Memory result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save memory result: {e!s}", cause=e)
