"""Monitoring module for tracking agent performance and decision-making processes.

This module provides functionality for monitoring agent performance metrics,
logging decision-making processes, and auditing agent behavior.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core.errors import PepperpyError
from ..interfaces import BaseProvider

logger = logging.getLogger(__name__)

class MonitoringError(PepperpyError):
    """Monitoring error."""
    pass

# Re-export Monitor from core
from ..core.monitoring.monitor import Monitor

__all__ = [
    "MonitoringError",
    "Monitor",
]
