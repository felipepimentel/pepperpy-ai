"""
PepperPy Core.

Core components of the PepperPy framework including configuration,
logging, errors, and plugin system.
"""

# Import core utilities to expose them at the package level
from pepperpy.core.config import (
    PepperPyConfig,
    get_component_config,
    get_config,
    get_default_provider,
    get_environment,
    get_plugin_configuration,
    get_provider_api_key,
    get_provider_config,
    initialize_config,
    is_development,
    is_production,
)
from pepperpy.core.context import (
    ContextError,
    ExecutionContext,
    execution_context,
    get_current_context,
    with_context,
)
from pepperpy.core.errors import (
    ConfigurationError,
    PepperpyError,
    PluginError,
    ProviderError,
    ValidationError,
)
from pepperpy.core.logging import configure_logging, get_logger
from pepperpy.core.observability import (
    Metric,
    MetricType,
    ObservabilityError,
    create_counter,
    create_gauge,
    create_histogram,
    get_metric,
    get_metrics_registry,
    instrument,
    timed_operation,
)

__all__ = [
    # Configuration
    "get_config",
    "initialize_config",
    "get_component_config",
    "get_provider_config",
    "get_provider_api_key",
    "get_default_provider",
    "get_environment",
    "is_development",
    "is_production",
    "PepperPyConfig",
    "get_plugin_configuration",
    # Context
    "ContextError",
    "ExecutionContext",
    "execution_context",
    "get_current_context",
    "with_context",
    # Errors
    "PepperpyError",
    "ConfigurationError",
    "ValidationError",
    "PluginError",
    "ProviderError",
    # Logging
    "get_logger",
    "configure_logging",
    # Observability
    "Metric",
    "MetricType",
    "ObservabilityError",
    "create_counter",
    "create_gauge",
    "create_histogram",
    "get_metric",
    "get_metrics_registry",
    "instrument",
    "timed_operation",
]
