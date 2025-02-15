"""Pepperpy - A Python library for building AI-powered research assistants.

This module provides a high-level API for creating and managing AI agents
specialized in research tasks, including topic analysis, source discovery,
and information synthesis.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Union, cast
from uuid import uuid4

from loguru import logger

from pepperpy.core.base import BaseAgent
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.hub import Hub as PepperpyHub
from pepperpy.core.hub.base import Hub, HubConfig, HubType
from pepperpy.core.types import Message, MessageType, Response
from pepperpy.core.workflows import WorkflowEngine, WorkflowStep

__version__ = "0.1.0"

# Configure logger
logger.add("pepperpy.log", rotation="500 MB")

__all__ = [
    "Pepperpy",
    "BaseAgent",
    "PepperpyClient",
    "PepperpyConfig",
    "Message",
    "MessageType",
    "Response",
    "Hub",
    "HubConfig",
    "HubType",
    "WorkflowEngine",
    "WorkflowStep",
]


class Pepperpy:
    """Main entry point for the Pepperpy library.

    This class provides a simplified interface for using Pepperpy's capabilities.
    """

    def __init__(self, client: Optional[PepperpyClient] = None):
        """Initialize Pepperpy with an optional client."""
        self._client: Optional[PepperpyClient] = client
        self._initialized = False
        self._interactive = False

    @classmethod
    async def create(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> "Pepperpy":
        """Create a new Pepperpy instance with minimal configuration."""
        # Create instance
        instance = cls()

        # Setup config with defaults
        config = {"api_key": api_key, "model": model, **kwargs}

        # Create and initialize client
        client = PepperpyClient(config=config)
        await client.initialize()

        # Store client
        instance._client = client
        instance._initialized = True

        return instance

    @property
    def hub(self) -> PepperpyHub:
        """Get the hub instance."""
        return PepperpyHub(
            name="local",
            config=HubConfig(
                type=HubType.LOCAL,
                resources=[],
                workflows=[],
                metadata={},
                root_dir=None,
            ),
        )

    async def __aenter__(self) -> "Pepperpy":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.cleanup()

    async def ask(self, question: str, **kwargs: Any) -> str:
        """Ask a question and get a response."""
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        kwargs.setdefault("temperature", 0.7)
        kwargs.setdefault("max_tokens", 2048)

        try:
            return await self._client.chat(question, **kwargs)
        except Exception as e:
            logger.error(
                "Failed to get response",
                error=str(e),
                question=question[:100],
                **kwargs,
            )
            raise


class ResearchResult:
    """Container for research results."""

    def __init__(self, data: dict):
        """Initialize with research data."""
        self._data = data

    @property
    def tldr(self) -> str:
        """Get a short summary."""
        return self._data.get("tldr", "")

    @property
    def full(self) -> str:
        """Get the full research report."""
        return self._data.get("full", "")

    @property
    def bullets(self) -> list[str]:
        """Get key points as bullet points."""
        return self._data.get("bullets", [])

    @property
    def references(self) -> list[dict]:
        """Get cited references with metadata."""
        return self._data.get("references", [])
