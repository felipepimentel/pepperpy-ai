"""Data providers for PepperPy.

This module provides data providers for different data sources and databases.
"""

from pepperpy.core.logging import get_logger

# Setup logging
logger = get_logger(__name__)


# Stub for any providers that might have external dependencies
class DataProvider:
    """Base class for data providers."""

    pass


NoSQLProvider = DataProvider
SQLProvider = DataProvider
RESTProvider = DataProvider
CloudProvider = DataProvider
FileProvider = DataProvider

__all__ = [
    "DataProvider",
    "NoSQLProvider",
    "SQLProvider",
    "RESTProvider",
    "CloudProvider",
    "FileProvider",
]
