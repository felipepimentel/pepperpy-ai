"""Protocols and interfaces for PepperPy

This module defines the fundamental protocols and interfaces of the framework,
including:

- Lifecycle
  - Initialization
  - Execution
  - Finalization
  - States

- Capabilities
  - Serialization
  - Validation
  - Observability
  - Configuration

- Communication
  - Events
  - Messages
  - Callbacks
  - Streams

Protocols are essential for:
- Defining clear contracts
- Ensuring extensibility
- Allowing polymorphism
- Facilitating testing
"""

from typing import Dict, List, Optional, Protocol, Union

from .lifecycle import Lifecycle
from .messaging import MessageHandler
from .observable import Observable, Observer
from .serialization import Serializable
from .validation import Validatable

__version__ = "0.1.0"
__all__ = [
    "Lifecycle",
    "MessageHandler",
    "Observable",
    "Observer",
    "Serializable",
    "Validatable",
]
