"""Common types and utilities for PepperPy.

This module provides common types and utilities used throughout the PepperPy framework,
including enums, dataclasses, and type aliases.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.utils.base import generate_id

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


def create_resource_id() -> ResourceID:
    """Create a unique resource ID.

    Returns:
        A unique resource ID
    """
    return generate_id()


def create_metadata(
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> Metadata:
    """Create metadata for a resource.

    Args:
        name: Human-readable name for the resource
        description: Description of the resource
        tags: Tags associated with the resource
        custom: Custom metadata

    Returns:
        Metadata object
    """
    return Metadata(
        id=create_resource_id(),
        name=name,
        description=description,
        tags=tags or [],
        custom=custom or {},
    )


def create_resource(
    type_: ResourceType,
    name: Optional[str] = None,
    description: Optional[str] = None,
    content: Optional[Any] = None,
    uri: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> Resource:
    """Create a resource.

    Args:
        type_: Type of the resource
        name: Human-readable name for the resource
        description: Description of the resource
        content: Content of the resource
        uri: URI of the resource
        tags: Tags associated with the resource
        custom: Custom metadata

    Returns:
        Resource object
    """
    metadata = create_metadata(name, description, tags, custom)
    return Resource(type=type_, metadata=metadata, content=content, uri=uri)


def create_result(
    status: StatusCode,
    data: Optional[Any] = None,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Result:
    """Create a result.

    Args:
        status: Status of the operation
        data: Data returned by the operation
        message: Message describing the result
        metadata: Metadata for the result

    Returns:
        Result object
    """
    return Result(
        status=status,
        data=data,
        message=message,
        metadata=metadata or {},
    )


__all__ = [
    # Type aliases
    "JSON",
    "PathType",
    # Resource IDs
    "ResourceID",
    "ApplicationID",
    "ModelID",
    "EmbeddingID",
    "VectorStoreID",
    "KnowledgeBaseID",
    "WorkflowID",
    "UserID",
    "OrganizationID",
    # Enums
    "ResourceType",
    "ContentType",
    "OperationType",
    "StatusCode",
    # Classes
    "Metadata",
    "Resource",
    "Result",
    # Functions
    "create_resource_id",
    "create_metadata",
    "create_resource",
    "create_result",
]
