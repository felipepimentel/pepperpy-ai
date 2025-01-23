"""System-wide constants for Pepperpy framework."""

from enum import Enum, auto
from typing import Final

# Version information
VERSION: Final[str] = "0.1.0"
API_VERSION: Final[str] = "v1"

# System paths
DEFAULT_CONFIG_DIR: Final[str] = "~/.pepperpy"
DEFAULT_CACHE_DIR: Final[str] = "~/.pepperpy/cache"
DEFAULT_LOG_DIR: Final[str] = "~/.pepperpy/logs"

# System limits
MAX_CONTEXT_SIZE: Final[int] = 4096
MAX_HISTORY_SIZE: Final[int] = 1000
DEFAULT_BATCH_SIZE: Final[int] = 32

# Timeouts (in seconds)
DEFAULT_TIMEOUT: Final[float] = 30.0
LONG_TIMEOUT: Final[float] = 120.0
CONNECTION_TIMEOUT: Final[float] = 10.0

class LogLevel(str, Enum):
    """Log levels for the system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ComponentState(str, Enum):
    """Component lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ERROR = "error"
    TERMINATING = "terminating"
    TERMINATED = "terminated"

class ProviderType(str, Enum):
    """Types of providers in the system."""
    LLM = "llm"
    EMBEDDING = "embedding"
    VECTOR_STORE = "vector_store"
    MEMORY = "memory"
    REASONING = "reasoning"

class ErrorCode(str, Enum):
    """System error codes."""
    INITIALIZATION_ERROR = "INIT_001"
    CONFIGURATION_ERROR = "CONF_001"
    PROVIDER_ERROR = "PROV_001"
    VALIDATION_ERROR = "VAL_001"
    RUNTIME_ERROR = "RUN_001"
    TIMEOUT_ERROR = "TIME_001"
