"""Datastore module for external data store integration.

This module provides functionality for connecting to and interacting with
external data stores.
"""

from .datastore import DataStore, DataStoreError
from .connector import DataStoreConnector, ConnectorError

__all__ = [
    "DataStore",
    "DataStoreError",
    "DataStoreConnector",
    "ConnectorError",
] 