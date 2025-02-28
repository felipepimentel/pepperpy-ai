"""Core utilities and helper functions.

This module provides utilities and helper functions used throughout the framework,
including:

- Data Manipulation
  - Type conversion
  - Data validation
  - Serialization
  - Formatting

- Resource Management
  - Allocation
  - Cleanup
  - Monitoring
  - Caching

- Optimizations
  - Performance
  - Memory
  - I/O
  - Concurrency

The module is designed to:
- Centralize common functions
- Avoid duplication
- Standardize operations
- Facilitate maintenance
"""

from typing import Dict, List, Optional, Union

from .data import DataUtils
from .data_manipulation import (
    DataUtils as DataUtilsNew,
)
from .data_manipulation import (
    DateUtils,
    DictUtils,
    ListUtils,
    NumberUtils,
    StringUtils,
)

# These modules are planned but not yet implemented with proper classes
# from .io import IOUtils
# from .system import SystemUtils
# from .validation import ValidationUtils
from .serialization import CsvUtils, JsonUtils, SerializationUtils, XmlUtils, YamlUtils

__version__ = "0.1.0"
__all__ = [
    "DataUtils",
    # "IOUtils",
    # "SystemUtils",
    # "ValidationUtils",
    "SerializationUtils",
    "JsonUtils",
    "YamlUtils",
    "XmlUtils",
    "CsvUtils",
    "StringUtils",
    "NumberUtils",
    "DateUtils",
    "DictUtils",
    "ListUtils",
    "DataUtilsNew",
]
