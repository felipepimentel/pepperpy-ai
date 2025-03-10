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

# Import from common module - will be available once the module is fully implemented
"""
from pepperpy.core.common import (
    ContentType,
    Metadata,
    OperationType,
    Resource,
    ResourceType,
    Result,
    StatusCode,
    JSON,
    Path,
    ResourceID,
    UserID,
    OrganizationID,
    ApplicationID,
    WorkflowID,
    ModelID,
    EmbeddingID,
    VectorStoreID,
    KnowledgeBaseID,
    generate_id,
    generate_timestamp,
    hash_string,
    load_json,
    save_json,
    slugify,
    truncate_string,
    retry,
    is_valid_email,
    is_valid_url,
    get_file_extension,
    get_file_size,
    get_file_mime_type,
)
"""

# Import from interfaces module - will be available once the module is fully implemented
"""
from pepperpy.core.interfaces import (
    Configurable,
    Initializable,
    Cleanable,
    Serializable,
    Provider,
    ResourceProvider,
    Processor,
    Transformer,
    Analyzer,
    Generator,
    Validator,
)
"""

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
    # Types - commented out until fully implemented
    """
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
    """,
    # Utilities - commented out until fully implemented
    """
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
    """,
    # Interfaces - commented out until fully implemented
    """
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
    """,
]
