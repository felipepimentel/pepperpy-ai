"""Tools module for Pepperpy framework.

This module provides a collection of reusable tools that can be used by agents
to perform specific tasks or operations.
"""

from pepperpy.capabilities.tools.base import BaseTool, ToolConfig, ToolError
from pepperpy.capabilities.tools.functions.core import APITool, CircuitBreaker, TokenHandler
from pepperpy.capabilities.tools.functions.io import FileHandler, CodeHandler, SearchHandler, ShellHandler, DocumentLoader
from pepperpy.capabilities.tools.functions.ai import LLMManager, BaseLLM, StabilityAI, VisionHandler, SerpHandler
from pepperpy.capabilities.tools.functions.media import ElevenLabs
from pepperpy.capabilities.tools.functions.system import TerminalHandler

__all__ = [
    # Base
    'BaseTool',
    'ToolConfig',
    'ToolError',
    # Core
    'APITool',
    'CircuitBreaker',
    'TokenHandler',
    # IO
    'FileHandler',
    'CodeHandler',
    'SearchHandler',
    'ShellHandler',
    'DocumentLoader',
    # AI
    'LLMManager',
    'BaseLLM',
    'StabilityAI',
    'VisionHandler',
    'SerpHandler',
    # Media
    'ElevenLabs',
    # System
    'TerminalHandler',
]
