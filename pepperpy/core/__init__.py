"""Core functionality for PepperPy.

This module provides the core functionality for PepperPy, including:
- Base models and interfaces
- Error handling
- Configuration management
- Validation utilities
- Logging and metrics
- Utility functions
"""

from pepperpy.core.base import (
    BaseComponent,
    BaseProvider,
    Component,
    ComponentError,
    ComponentRegistry,
    ConfigurationError,
    ConnectionError,
    Document,
    GenerationResult,
    HTTPError,
    JsonDict,
    JsonType,
    JsonValue,
    LLMProvider,
    Metadata,
    PepperpyError,
    ProviderError,
    QueryParamsType,
    RAGProvider,
    RequestError,
    ResponseError,
    SearchResult,
    StorageProvider,
    TimeoutError,
    ValidationError,
    WorkflowProvider,
)
from pepperpy.core.config import Config
from pepperpy.core.di import Container
from pepperpy.core.logging import get_logger, logger
from pepperpy.core.memory import BaseMemory
from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.utils import (
    BaseProvider as UtilsBaseProvider,
)
from pepperpy.core.utils import (
    ConfigError,
)
from pepperpy.core.utils import (
    PepperpyError as UtilsPepperpyError,
)
from pepperpy.core.utils import (
    ProviderError as UtilsProviderError,
)
from pepperpy.core.utils import (
    ValidationError as UtilsValidationError,
)

# Import helper functions
try:
    from pepperpy.core.helpers import (
        convert_to_dict,
        flatten_dict,
        format_date,
        get_class_attributes,
        import_string,
        merge_configs,
        retry,
        safe_import,
        truncate_text,
        unflatten_dict,
        validate_type,
    )
except ImportError:
    # Define empty helper functions with proper type hints
    from datetime import datetime
    from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

    T = TypeVar("T")

    def convert_to_dict(obj: Any) -> Dict[str, Any]:
        return getattr(obj, "__dict__", {})

    def flatten_dict(
        d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        return d

    def format_date(
        dt: Optional[Union[datetime, str]] = None, fmt: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        return ""

    def get_class_attributes(obj: Any) -> Dict[str, Any]:
        return {}

    def import_string(dotted_path: str) -> Any:
        return None

    def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        return {**base, **override}

    def retry(
        max_tries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
        hook: Optional[Callable[[Exception, int], None]] = None,
    ) -> Callable:
        return lambda f: f

    def safe_import(module_name: str) -> Optional[Any]:
        return None

    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        return text

    def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
        return d

    def validate_type(value: Any, expected_type: Type[T]) -> T:
        return value


from pepperpy.core.validation import validate_config
from pepperpy.core.version import __version__

# Re-export error types for convenience
# ConfigError = ConfigurationError
# Já está definido em utils.py

__all__ = [
    # Base
    "BaseComponent",
    # Memory
    "BaseMemory",
    "BaseProvider",
    "Component",
    "ComponentError",
    "ComponentRegistry",
    # Config
    "Config",
    "ConfigError",  # Alias para ConfigurationError
    "ConfigurationError",
    # Errors
    "ConnectionError",
    # DI
    "Container",
    # Types
    "Document",
    "GenerationResult",
    "HTTPError",
    "JsonDict",
    "JsonType",
    "JsonValue",
    "LLMProvider",
    "Metadata",
    # Metrics
    "MetricsCollector",
    "PepperpyError",
    "ProviderError",
    "QueryParamsType",
    "RAGProvider",
    "RequestError",
    "ResponseError",
    "SearchResult",
    "StorageProvider",
    "TimeoutError",
    "ValidationError",
    "WorkflowProvider",
    # Version
    "__version__",
    # Logging
    "get_logger",
    "logger",
    # Validation
    "validate_config",
    # Legado (core.py)
    "ConfigError",
    "UtilsBaseProvider",
    "UtilsPepperpyError",
    "UtilsProviderError",
    "UtilsValidationError",
    # Helper functions
    "convert_to_dict",
    "flatten_dict",
    "format_date",
    "get_class_attributes",
    "import_string",
    "merge_configs",
    "retry",
    "safe_import",
    "truncate_text",
    "unflatten_dict",
    "validate_type",
]

# Adicionar as funções auxiliares ao __all__ apenas se existirem
try:
    __all__.extend(
        [
            "convert_to_dict",
            "flatten_dict",
            "format_date",
            "get_class_attributes",
            "import_string",
            "merge_configs",
            "retry",
            "safe_import",
            "truncate_text",
            "unflatten_dict",
            "validate_type",
        ]
    )
except NameError:
    pass
