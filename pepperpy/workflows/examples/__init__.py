"""Workflow implementation examples.

This module provides practical examples of workflow implementations,
demonstrating:

- Workflow Types
  - Simple workflows
  - Complex workflows
  - Parallel workflows
  - Nested workflows

- Implementation Patterns
  - Step definition
  - Execution configuration
  - Error handling
  - Callbacks and events

- Use Cases
  - Data processing
  - Service integration
  - Task automation
  - Agent orchestration

The examples serve to:
- Demonstrate functionality
- Illustrate best practices
- Facilitate learning
- Validate implementations
"""

from typing import Dict, List, Optional, Union

from .actions import (
    DelayAction,
    HelloWorldAction,
    ListProcessorAction,
    RandomNumberAction,
    register_example_actions,
)
from .hello_world import HelloWorldWorkflow

__version__ = "0.1.0"
__all__ = [
    # Actions
    "DelayAction",
    "HelloWorldAction",
    "ListProcessorAction",
    "RandomNumberAction",
    "register_example_actions",
    # Workflows
    "HelloWorldWorkflow",
]
