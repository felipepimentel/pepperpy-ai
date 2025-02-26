"""Configuration types and constants."""

from typing import Any, Dict, List, Union

# Basic configuration value types
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]

# Configuration provider types
CONFIG_PROVIDER_FILE = "file"
CONFIG_PROVIDER_ENV = "env"
CONFIG_PROVIDER_SECURE = "secure"

# Environment types
ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"
ENV_TEST = "test"

# Configuration namespaces
CONFIG_NAMESPACE_CORE = "core"
CONFIG_NAMESPACE_APP = "app"
CONFIG_NAMESPACE_USER = "user"
CONFIG_NAMESPACE_SYSTEM = "system"
