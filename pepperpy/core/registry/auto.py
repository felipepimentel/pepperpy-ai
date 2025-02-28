"""Auto-registration utilities for the registry system.

This module provides utilities for automatically registering components
with the registry system based on decorators and module scanning.
"""

import importlib
import inspect
import logging
import pkgutil
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from pepperpy.common.registry.base import (
    ComponentMetadata,
    Registry,
    RegistryComponent,
    auto_register,
    get_registry,
) 