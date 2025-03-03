"""Core enumerations.

Defines enumerations used throughout the framework.
"""

from enum import Enum, auto
from uuid import UUID


class ComponentState(Enum):
    """Component execution states."""

    UNKNOWN = auto()
    INITIALIZING = auto()
    READY = auto()
    EXECUTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()
    CLEANED = auto()
    UNREGISTERED = auto()


class AgentState(Enum):
    """Agent execution states."""

    UNKNOWN = auto()
    INITIALIZING = auto()
    READY = auto()
    EXECUTING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()
    CLEANED = auto()


# Type aliases for IDs
AgentID = UUID
CapabilityID = UUID
ProviderID = UUID
ResourceID = UUID
WorkflowID = UUID

# Re-export AgentState from agents module to avoid circular imports


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


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class WorkflowPriority(Enum):
    """Workflow execution priority."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()
