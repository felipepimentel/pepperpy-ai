"""Base constants for Pepperpy."""

from enum import Enum, auto
from typing import Final

# Version information
VERSION: Final[str] = "0.1.0"
AUTHOR: Final[str] = "Pepperpy Team"
LICENSE: Final[str] = "MIT"

# Environment variables
ENV_PREFIX: Final[str] = "PEPPERPY_"
CONFIG_PATH_ENV: Final[str] = f"{ENV_PREFIX}CONFIG_PATH"
LOG_LEVEL_ENV: Final[str] = f"{ENV_PREFIX}LOG_LEVEL"
LOG_FORMAT_ENV: Final[str] = f"{ENV_PREFIX}LOG_FORMAT"

# Default paths
DEFAULT_CONFIG_PATH: Final[str] = "config/default_config.yaml"
DEFAULT_LOG_PATH: Final[str] = "logs/pepperpy.log"
DEFAULT_CACHE_PATH: Final[str] = "cache"
DEFAULT_DATA_PATH: Final[str] = "data"

# Default values
DEFAULT_CHUNK_SIZE: Final[int] = 1000
DEFAULT_CHUNK_OVERLAP: Final[int] = 200
DEFAULT_BATCH_SIZE: Final[int] = 32
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_RETRIES: Final[int] = 3
DEFAULT_BACKOFF: Final[float] = 1.5

# Status codes
class Status(str, Enum):
    """Status codes for operations."""
    
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

# Operation types
class Operation(str, Enum):
    """Types of operations."""
    
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    TRAIN = "train"
    PREDICT = "predict"
    EMBED = "embed"

# Resource types
class ResourceType(str, Enum):
    """Types of resources."""
    
    MODEL = "model"
    DOCUMENT = "document"
    VECTOR = "vector"
    MEMORY = "memory"
    EXAMPLE = "example"
    WORKFLOW = "workflow"
    STRATEGY = "strategy"
    CONFIG = "config"

# Environment types
class Environment(str, Enum):
    """Types of environments."""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# Log levels
class LogLevel(str, Enum):
    """Log levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL" 