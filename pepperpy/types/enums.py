"""Core enums for the Pepperpy project.

This module defines enums used throughout the project.
"""

from enum import Enum, auto


class ProviderType(Enum):
    """Types of AI providers."""

    OPENAI = auto()
    ANTHROPIC = auto()
    GOOGLE = auto()
    CUSTOM = auto()


class IndexType(Enum):
    """Types of search indexes."""

    VECTOR = auto()
    TEXT = auto()
    HYBRID = auto()


class LogLevel(Enum):
    """Log levels for the logging system."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class TaskStatus(Enum):
    """Status of a task in the system."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class ResourceType(Enum):
    """Types of resources in the system."""

    AGENT = auto()
    WORKFLOW = auto()
    MEMORY = auto()
    INDEX = auto()
    PLUGIN = auto()
    MODEL = auto()


class ErrorCategory(Enum):
    """Categories of errors that can occur."""

    VALIDATION = auto()
    CONFIGURATION = auto()
    PROVIDER = auto()
    RESOURCE = auto()
    OPERATION = auto()
    SYSTEM = auto()
