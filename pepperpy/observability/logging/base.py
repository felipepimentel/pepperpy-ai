"""Base logging module for the Pepperpy framework.

This module provides core logging functionality including:
- Centralized logging configuration
- Structured logging with context
- Asynchronous logging support
- Customizable formatters and handlers

@file: base.py
@purpose: Core logging functionality
@component: Core/Logging
@created: 2024-02-25
@task: TASK-007-R020
@status: completed
"""

import asyncio
import logging
from typing import Any, TypeVar

from pepperpy.core.errors import ValidationError
from pepperpy.core.common.lifecycle.types import Lifecycle
from pepperpy.core.types import ComponentState

# Configure base logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Type variables
T = TypeVar("T", bound="LogRecord")

# Lazy imports
_BaseModel = None
_Field = None


def get_model_imports():
    """Get model imports lazily."""
    global _BaseModel, _Field
    if _BaseModel is None or _Field is None:
        from pepperpy.core.common.models import BaseModel, Field

        _BaseModel = BaseModel
        _Field = Field
    return _BaseModel, _Field


class LogLevel:
    """Log level type."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_str(cls, level: str) -> int:
        """Convert string level to logging level.

        Args:
            level: Level string

        Returns:
            Logging level

        Raises:
            ValidationError: If level is invalid
        """
        level_map = {
            "DEBUG": cls.DEBUG,
            "INFO": cls.INFO,
            "WARNING": cls.WARNING,
            "ERROR": cls.ERROR,
            "CRITICAL": cls.CRITICAL,
        }
        if level not in level_map:
            raise ValidationError(f"Invalid log level: {level}")
        return level_map[level]

    @classmethod
    def to_str(cls, level: int) -> str:
        """Convert logging level to string.

        Args:
            level: Logging level

        Returns:
            Level string

        Raises:
            ValidationError: If level is invalid
        """
        level_map = {
            cls.DEBUG: "DEBUG",
            cls.INFO: "INFO",
            cls.WARNING: "WARNING",
            cls.ERROR: "ERROR",
            cls.CRITICAL: "CRITICAL",
        }
        if level not in level_map:
            raise ValidationError(f"Invalid log level: {level}")
        return level_map[level]


class LogRecord:
    """Log record model.

    Attributes:
        level: Log level (int or str)
        logger: Logger name
        message: Log message
        context: Log context
        exception: Exception if any
    """

    def __init__(
        self,
        level: int | str = LogLevel.INFO,
        logger: str = "root",
        message: str = "",
        context: dict[str, Any] | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Initialize log record.

        Args:
            level: Log level (int or str)
            logger: Logger name
            message: Log message
            context: Optional log context
            exception: Optional exception
        """
        BaseModel, Field = get_model_imports()
        self.level = LogLevel.from_str(level) if isinstance(level, str) else level
        self.logger = logger
        self.message = message
        self.context = context or {}
        self.exception = exception

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": LogLevel.to_str(self.level),
            "logger": self.logger,
            "message": self.message,
            "context": self.context,
            "exception": str(self.exception) if self.exception else None,
        }


class LogHandler(Lifecycle):
    """Base log handler."""

    def __init__(self) -> None:
        """Initialize log handler."""
        self._state = ComponentState.CREATED
        self._queue: asyncio.Queue[LogRecord] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Initialize handler."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._process_logs())
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize handler: {e}")

    async def cleanup(self) -> None:
        """Clean up handler."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                await self._task
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up handler: {e}")

    async def _process_logs(self) -> None:
        """Process logs from queue."""
        while True:
            try:
                record = await self._queue.get()
                await self._handle_record(record)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Failed to process log record: {e}", exc_info=True)

    async def _handle_record(self, record: LogRecord) -> None:
        """Handle log record.

        Args:
            record: Log record to handle
        """
        raise NotImplementedError


class LogManager(Lifecycle):
    """Log manager."""

    def __init__(self) -> None:
        """Initialize log manager."""
        super().__init__()
        self._handlers: dict[str, LogHandler] = {}
        self._state = ComponentState.CREATED

    async def initialize(self) -> None:
        """Initialize manager."""
        try:
            self._state = ComponentState.INITIALIZING
            for handler in self._handlers.values():
                await handler.initialize()
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize manager: {e}")

    async def cleanup(self) -> None:
        """Clean up manager."""
        try:
            self._state = ComponentState.CLEANING
            for handler in self._handlers.values():
                await handler.cleanup()
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up manager: {e}")

    def add_handler(self, name: str, handler: LogHandler) -> None:
        """Add log handler.

        Args:
            name: Handler name
            handler: Log handler

        Raises:
            ValidationError: If handler already exists
        """
        if name in self._handlers:
            raise ValidationError(f"Handler already exists: {name}")
        self._handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """Remove log handler.

        Args:
            name: Handler name

        Raises:
            ValidationError: If handler does not exist
        """
        if name not in self._handlers:
            raise ValidationError(f"Handler does not exist: {name}")
        del self._handlers[name]

    def get_handler(self, name: str) -> LogHandler:
        """Get log handler.

        Args:
            name: Handler name

        Returns:
            Log handler

        Raises:
            ValidationError: If handler does not exist
        """
        if name not in self._handlers:
            raise ValidationError(f"Handler does not exist: {name}")
        return self._handlers[name]

    def has_handler(self, name: str) -> bool:
        """Check if handler exists.

        Args:
            name: Handler name

        Returns:
            True if handler exists, False otherwise
        """
        return name in self._handlers

    def get_handlers(self) -> list[LogHandler]:
        """Get all handlers.

        Returns:
            List of handlers
        """
        return list(self._handlers.values())
