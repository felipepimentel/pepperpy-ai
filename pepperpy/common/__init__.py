"""Common module for shared functionality.

This module provides common utilities, constants, types, and error handling
used throughout the Pepperpy framework.
"""

from enum import Enum, auto
from typing import Final

from .config import Config, ConfigError
from .errors import PepperpyError
from .types import PepperpyObject, DictInitializable, Validatable


# Base constants
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_BATCH_SIZE: Final[int] = 100
DEFAULT_CHUNK_SIZE: Final[int] = 1000
DEFAULT_CACHE_SIZE: Final[int] = 1000
DEFAULT_BUFFER_SIZE: Final[int] = 1024
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[int] = 1


class Status(Enum):
    """Status enum for various components."""
    INITIALIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()


# Learning constants
DEFAULT_LEARNING_RATE: Final[float] = 0.001
DEFAULT_EPOCHS: Final[int] = 10
DEFAULT_TRAIN_BATCH_SIZE: Final[int] = 32
DEFAULT_EVAL_BATCH_SIZE: Final[int] = 64
DEFAULT_VALIDATION_SPLIT: Final[float] = 0.2
DEFAULT_TEST_SPLIT: Final[float] = 0.1


class LearningMode(Enum):
    """Learning mode enum."""
    SUPERVISED = auto()
    UNSUPERVISED = auto()
    REINFORCEMENT = auto()
    ACTIVE = auto()


# Model constants
DEFAULT_MODEL_VERSION: Final[str] = "1.0.0"
DEFAULT_MODEL_PROVIDER: Final[str] = "pepperpy"
DEFAULT_MODEL_TIMEOUT: Final[int] = 60
DEFAULT_MODEL_MAX_TOKENS: Final[int] = 2048
DEFAULT_MODEL_TEMPERATURE: Final[float] = 0.7


class ModelType(Enum):
    """Model type enum."""
    LANGUAGE = auto()
    VISION = auto()
    AUDIO = auto()
    MULTIMODAL = auto()


# Storage constants
DEFAULT_STORAGE_PATH: Final[str] = "./data"
DEFAULT_INDEX_PATH: Final[str] = "./index"
DEFAULT_CACHE_PATH: Final[str] = "./cache"
DEFAULT_LOG_PATH: Final[str] = "./logs"
DEFAULT_MODEL_PATH: Final[str] = "./models"


class StorageType(Enum):
    """Storage type enum."""
    FILE = auto()
    MEMORY = auto()
    DATABASE = auto()
    CLOUD = auto()


__all__ = [
    # Base
    "PepperpyError",
    "PepperpyObject",
    "DictInitializable",
    "Validatable",
    # Config
    "Config",
    "ConfigError",
    # Constants
    "DEFAULT_TIMEOUT",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CACHE_SIZE",
    "DEFAULT_BUFFER_SIZE",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    # Enums
    "Status",
    "LearningMode",
    "ModelType",
    "StorageType",
    # Learning constants
    "DEFAULT_LEARNING_RATE",
    "DEFAULT_EPOCHS",
    "DEFAULT_TRAIN_BATCH_SIZE",
    "DEFAULT_EVAL_BATCH_SIZE",
    "DEFAULT_VALIDATION_SPLIT",
    "DEFAULT_TEST_SPLIT",
    # Model constants
    "DEFAULT_MODEL_VERSION",
    "DEFAULT_MODEL_PROVIDER",
    "DEFAULT_MODEL_TIMEOUT",
    "DEFAULT_MODEL_MAX_TOKENS",
    "DEFAULT_MODEL_TEMPERATURE",
    # Storage constants
    "DEFAULT_STORAGE_PATH",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_CACHE_PATH",
    "DEFAULT_LOG_PATH",
    "DEFAULT_MODEL_PATH",
]
