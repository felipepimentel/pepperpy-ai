"""Adapter management system for the Pepperpy framework.

This module provides comprehensive adapter management:
- Adapter discovery
- Adapter loading
- Adapter lifecycle
- Adapter monitoring
- Adapter factory
"""

from pepperpy.core.adapters.base import (
    Adapter,
    AdapterMetadata,
    AdapterState,
    AdapterType,
    NetworkAdapter,
    ProcessorAdapter,
    ProviderAdapter,
    StorageAdapter,
)
from pepperpy.core.adapters.factory import (
    AdapterFactory,
    NetworkAdapterFactory,
    ProcessorAdapterFactory,
    ProviderAdapterFactory,
    StorageAdapterFactory,
    network_adapter_factory,
    processor_adapter_factory,
    provider_adapter_factory,
    storage_adapter_factory,
)
from pepperpy.core.adapters.manager import (
    AdapterManager,
    adapter_manager,
)
from pepperpy.core.adapters.monitor import (
    AdapterMonitor,
    AdapterUsage,
    adapter_monitor,
)

# Export public API
__all__ = [
    # Adapter base
    "Adapter",
    "AdapterMetadata",
    "AdapterState",
    "AdapterType",
    "NetworkAdapter",
    "ProcessorAdapter",
    "ProviderAdapter",
    "StorageAdapter",
    # Adapter factory
    "AdapterFactory",
    "NetworkAdapterFactory",
    "ProcessorAdapterFactory",
    "ProviderAdapterFactory",
    "StorageAdapterFactory",
    "network_adapter_factory",
    "processor_adapter_factory",
    "provider_adapter_factory",
    "storage_adapter_factory",
    # Adapter management
    "AdapterManager",
    "adapter_manager",
    # Adapter monitoring
    "AdapterMonitor",
    "AdapterUsage",
    "adapter_monitor",
]
