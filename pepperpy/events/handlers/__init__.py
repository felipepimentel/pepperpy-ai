"""Event handlers package.

This package provides handlers for processing different types of events.
"""

from pepperpy.events.handlers.agent import AgentEventHandler
from pepperpy.events.handlers.workflow import WorkflowEventHandler

# Export public API
__all__ = [
    "AgentEventHandler",
    "WorkflowEventHandler",
]
