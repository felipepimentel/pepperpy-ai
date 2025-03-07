"""Adaptive workflows module for PepperPy.

This module provides tools and utilities for creating workflows that adapt
based on feedback and usage patterns.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.workflows.adaptive.feedback import (
    FeedbackCollector,
    FeedbackProcessor,
    FeedbackType,
)
from pepperpy.workflows.adaptive.learning import (
    AdaptiveWorkflow,
    create_adaptive_workflow,
    register_adaptive_workflow,
)

__all__ = [
    "AdaptiveWorkflow",
    "FeedbackCollector",
    "FeedbackProcessor",
    "FeedbackType",
    "create_adaptive_workflow",
    "register_adaptive_workflow",
]
