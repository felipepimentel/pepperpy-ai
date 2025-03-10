"""Assistant module for PepperPy.

This module provides base classes and utilities for creating assistants.
"""

# Ensure the directory exists
import os
from typing import Any, Dict, List, Optional, Union

os.makedirs(os.path.dirname(__file__), exist_ok=True)

# Export implementations
from pepperpy.core.assistant.implementations import ResearchAssistant

__all__ = ["ResearchAssistant"]
