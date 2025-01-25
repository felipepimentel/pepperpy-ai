"""
Persistence module for Pepperpy framework.

This module provides functionality for storing and retrieving data
with different storage backends and strategies.
"""

from pepperpy.persistence.base import BasePersistence, PersistenceError

__all__ = [
    "BasePersistence",
    "PersistenceError",
] 