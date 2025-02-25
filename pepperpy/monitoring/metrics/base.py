"""Base metrics functionality for the Pepperpy framework.

This module provides base classes for metrics functionality.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar

from pepperpy.core.models import BaseModel, Field
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics.unified import MetricsManager
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger

# Type variables
T = TypeVar("T")

# Initialize logger
logger = get_logger(__name__)

__all__ = ["MetricsManager"]
