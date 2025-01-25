"""
Core system constants and configuration values.
"""

from enum import Enum, auto
from typing import Dict, Final

# Version Information
VERSION: Final[str] = "0.1.0"
API_VERSION: Final[str] = "v1"

# System Constants
DEFAULT_ENCODING: Final[str] = "utf-8"
DEFAULT_CHUNK_SIZE: Final[int] = 1024
MAX_RETRIES: Final[int] = 3
DEFAULT_TIMEOUT: Final[int] = 30  # seconds
RATE_LIMIT_WINDOW: Final[int] = 3600  # seconds
RATE_LIMIT_MAX_REQUESTS: Final[int] = 1000
MAX_RETRY_ATTEMPTS: Final[int] = 3
DEFAULT_BATCH_SIZE: Final[int] = 100
DEFAULT_CACHE_TTL: Final[int] = 3600  # seconds

# Memory management
DEFAULT_MEMORY_LIMIT: Final[int] = 1024 * 1024 * 1024  # 1GB
DEFAULT_CACHE_SIZE: Final[int] = 1000  # items

# Provider settings
DEFAULT_PROVIDER_TIMEOUT: Final[int] = 60  # seconds
DEFAULT_PROVIDER_RETRIES: Final[int] = 3

# Security constants
TOKEN_EXPIRY: Final[int] = 3600  # seconds
MAX_TOKEN_REFRESH: Final[int] = 5
PASSWORD_MIN_LENGTH: Final[int] = 12

# API limits
MAX_REQUEST_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_RESPONSE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB

# Monitoring
METRICS_INTERVAL: Final[int] = 60  # seconds
HEALTH_CHECK_INTERVAL: Final[int] = 30  # seconds
ALERT_THRESHOLD: Final[int] = 90  # percentage

# Feature flags
ENABLE_NEW_STRUCTURE: Final[bool] = True
USE_LEGACY_PROVIDER: Final[bool] = False
FEATURES: Final[Dict[str, bool]] = {
    "ENABLE_CACHING": True,
    "ENABLE_METRICS": True,
    "ENABLE_TRACING": True,
    "ENABLE_RATE_LIMITING": True,
    "ENABLE_AUTO_SCALING": False,
    "ENABLE_ADVANCED_SECURITY": False,
}

# Path Constants
CONFIG_DIR: Final[str] = "config"
CACHE_DIR: Final[str] = "cache"
DATA_DIR: Final[str] = "data"
TEMP_DIR: Final[str] = "/tmp/pepperpy"

# File Limits
MAX_FILE_SIZE: Final[int] = 100 * 1024 * 1024  # 100MB


class ErrorCode(str, Enum):
    """Error codes for Pepperpy system."""
    CONFIGURATION_ERROR = "CONFIG_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    MIDDLEWARE_ERROR = "MIDDLEWARE_ERROR"
    EXTENSION_ERROR = "EXTENSION_ERROR"
    CAPABILITY_ERROR = "CAPABILITY_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    MONITORING_ERROR = "MONITORING_ERROR"


class ComponentState(str, Enum):
    """Component lifecycle states."""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class LogLevel(str, Enum):
    """Log levels for the system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Environment names."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class HTTPStatus(int, Enum):
    """Common HTTP status codes."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
