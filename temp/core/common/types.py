"""Common types for PepperPy.

This module defines common types used throughout the PepperPy framework,
including enums, dataclasses, and type aliases.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Type aliases
JSON = Dict[str, Any]
PathType = Union[str, Path]

# Resource IDs
ResourceID = str
ApplicationID = str
ModelID = str
EmbeddingID = str
VectorStoreID = str
KnowledgeBaseID = str
WorkflowID = str
UserID = str
OrganizationID = str


class ResourceType(str, Enum):
    """Types of resources in PepperPy."""

    FILE = "file"
    DIRECTORY = "directory"
    URL = "url"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"
    MODEL = "model"
    EMBEDDING = "embedding"
    VECTOR_STORE = "vector_store"
    KNOWLEDGE_BASE = "knowledge_base"
    WORKFLOW = "workflow"
    APPLICATION = "application"
    USER = "user"
    ORGANIZATION = "organization"
    CUSTOM = "custom"


class ContentType(str, Enum):
    """Types of content in PepperPy."""

    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    TSV = "tsv"
    YAML = "yaml"
    BINARY = "binary"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    CUSTOM = "custom"


class OperationType(str, Enum):
    """Types of operations in PepperPy."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    PROCESS = "process"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    GENERATE = "generate"
    EXECUTE = "execute"
    VALIDATE = "validate"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    CUSTOM = "custom"


class StatusCode(str, Enum):
    """Status codes for PepperPy operations."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INVALID = "invalid"
    CUSTOM = "custom"


@dataclass
class Metadata:
    """Metadata for PepperPy resources.

    Attributes:
        id: Unique identifier for the resource
        name: Human-readable name for the resource
        description: Description of the resource
        created_at: Timestamp when the resource was created
        updated_at: Timestamp when the resource was last updated
        tags: Tags associated with the resource
        custom: Custom metadata
    """

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Base class for PepperPy resources.

    Attributes:
        type: Type of the resource
        metadata: Metadata for the resource
        content: Content of the resource
        uri: URI of the resource
    """

    type: ResourceType
    metadata: Metadata
    content: Optional[Any] = None
    uri: Optional[str] = None


@dataclass
class Result:
    """Result of a PepperPy operation.

    Attributes:
        status: Status of the operation
        data: Data returned by the operation
        message: Message describing the result
        metadata: Metadata for the result
    """

    status: StatusCode
    data: Optional[Any] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
