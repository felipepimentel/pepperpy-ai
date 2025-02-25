"""Metric collectors for the Pepperpy framework.

This module provides collectors for gathering metrics from various sources.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pepperpy.core.models import BaseModel, Field
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics.unified import MetricsManager
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

__all__ = ["MetricsManager"]
