"""Public interfaces for PepperPy Core module.

This module provides a stable public interface for the Core functionality.
It exposes the core abstractions and implementations that are
considered part of the public API.
"""

# Import from core module
from pepperpy.core.core import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    PepperPyError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
    ensure_dir,
    get_config_dir,
    get_data_dir,
    get_env_var,
    get_logger,
    get_output_dir,
    get_project_root,
)


# Import from common module
# Implementação temporária para resolver problemas de importação
class ContentType:
    """Content type enumeration."""

    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    HTML = "html"
    MARKDOWN = "markdown"


class Metadata(dict):
    """Metadata container."""

    pass


class OperationType:
    """Operation type enumeration."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"


class Resource:
    """Base resource class."""

    def __init__(self, id=None, type=None, data=None, metadata=None):
        self.id = id
        self.type = type
        self.data = data or {}
        self.metadata = metadata or {}


class ResourceType:
    """Resource type enumeration."""

    DOCUMENT = "document"
    MEMORY = "memory"
    VECTOR = "vector"
    USER = "user"
    ORGANIZATION = "organization"
    APPLICATION = "application"
    WORKFLOW = "workflow"
    MODEL = "model"
    EMBEDDING = "embedding"
    VECTOR_STORE = "vector_store"
    KNOWLEDGE_BASE = "knowledge_base"


class Result:
    """Operation result container."""

    def __init__(self, success=True, data=None, error=None, metadata=None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}


class StatusCode:
    """HTTP-like status codes."""

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# Type aliases
JSON = dict
Path = str
ResourceID = str
UserID = str
OrganizationID = str
ApplicationID = str
WorkflowID = str
ModelID = str
EmbeddingID = str
VectorStoreID = str
KnowledgeBaseID = str


# Utility functions
def generate_id(prefix="", length=16):
    """Generate a unique ID."""
    import uuid

    return f"{prefix}{uuid.uuid4().hex[:length]}"


def generate_timestamp():
    """Generate a timestamp."""
    import datetime

    return datetime.datetime.now().isoformat()


def hash_string(s):
    """Hash a string."""
    import hashlib

    return hashlib.sha256(s.encode()).hexdigest()


def load_json(path):
    """Load JSON from a file."""
    import json

    with open(path, "r") as f:
        return json.load(f)


def save_json(data, path):
    """Save JSON to a file."""
    import json

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def slugify(s):
    """Convert a string to a slug."""
    import re

    return re.sub(r"[^\w\s-]", "", s.lower()).strip().replace(" ", "-")


def truncate_string(s, max_length=100):
    """Truncate a string to a maximum length."""
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."


def retry(max_attempts=3, delay=1):
    """Retry decorator."""
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator


def is_valid_email(email):
    """Check if a string is a valid email."""
    import re

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))


def is_valid_url(url):
    """Check if a string is a valid URL."""
    import re

    pattern = r"^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[-\w%!$&\'()*+,;=:]+)*$"
    return bool(re.match(pattern, url))


def get_file_extension(path):
    """Get the extension of a file."""
    import os

    return os.path.splitext(path)[1]


def get_file_size(path):
    """Get the size of a file in bytes."""
    import os

    return os.path.getsize(path)


def get_file_mime_type(path):
    """Get the MIME type of a file."""
    import mimetypes

    return mimetypes.guess_type(path)[0]


# Import from interfaces module
# Implementação temporária para resolver problemas de importação
class Configurable:
    """Interface for configurable components."""

    def configure(self, config):
        """Configure the component."""
        raise NotImplementedError


class Initializable:
    """Interface for initializable components."""

    async def initialize(self):
        """Initialize the component."""
        raise NotImplementedError


class Cleanable:
    """Interface for cleanable components."""

    async def cleanup(self):
        """Clean up resources."""
        raise NotImplementedError


class Serializable:
    """Interface for serializable components."""

    def to_dict(self):
        """Convert to dictionary."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        raise NotImplementedError


class Provider:
    """Base provider interface."""

    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}


class ResourceProvider(Provider):
    """Resource provider interface."""

    async def get(self, id):
        """Get a resource by ID."""
        raise NotImplementedError

    async def create(self, data):
        """Create a resource."""
        raise NotImplementedError

    async def update(self, id, data):
        """Update a resource."""
        raise NotImplementedError

    async def delete(self, id):
        """Delete a resource."""
        raise NotImplementedError

    async def list(self, filter=None):
        """List resources."""
        raise NotImplementedError


class Processor:
    """Base processor interface."""

    async def process(self, input_data):
        """Process input data."""
        raise NotImplementedError


class Transformer(Processor):
    """Transformer interface."""

    async def transform(self, input_data):
        """Transform input data."""
        raise NotImplementedError


class Analyzer(Processor):
    """Analyzer interface."""

    async def analyze(self, input_data):
        """Analyze input data."""
        raise NotImplementedError


class Generator(Processor):
    """Generator interface."""

    async def generate(self, input_data):
        """Generate output from input data."""
        raise NotImplementedError


class Validator(Processor):
    """Validator interface."""

    async def validate(self, input_data):
        """Validate input data."""
        raise NotImplementedError


# Re-export everything
__all__ = [
    # Errors
    "PepperPyError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
    # Utility functions
    "get_logger",
    "get_env_var",
    "get_project_root",
    "get_config_dir",
    "get_data_dir",
    "get_output_dir",
    "ensure_dir",
    # Types
    "ContentType",
    "Metadata",
    "OperationType",
    "Resource",
    "ResourceType",
    "Result",
    "StatusCode",
    "JSON",
    "Path",
    "ResourceID",
    "UserID",
    "OrganizationID",
    "ApplicationID",
    "WorkflowID",
    "ModelID",
    "EmbeddingID",
    "VectorStoreID",
    "KnowledgeBaseID",
    # Utilities
    "generate_id",
    "generate_timestamp",
    "hash_string",
    "load_json",
    "save_json",
    "slugify",
    "truncate_string",
    "retry",
    "is_valid_email",
    "is_valid_url",
    "get_file_extension",
    "get_file_size",
    "get_file_mime_type",
    # Interfaces
    "Configurable",
    "Initializable",
    "Cleanable",
    "Serializable",
    "Provider",
    "ResourceProvider",
    "Processor",
    "Transformer",
    "Analyzer",
    "Generator",
    "Validator",
]
