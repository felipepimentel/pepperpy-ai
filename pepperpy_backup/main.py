"""Main module for PepperPy."""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.llms.llm_manager import LLMManager


# Load environment variables
load_dotenv()


class PepperPy:
    """Main class for PepperPy."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PepperPy.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agent: Optional[BaseAgent] = None
        self.llm_manager = LLMManager()

    async def initialize(self) -> None:
        """Initialize PepperPy."""
        # Initialize LLM configuration with primary and fallback providers
        llm_config = {
            "primary": {
                "type": os.getenv("PEPPERPY_PROVIDER", "openrouter"),
                "model_name": os.getenv("PEPPERPY_MODEL", "anthropic/claude-2"),
                "api_key": os.getenv("PEPPERPY_API_KEY", ""),
                "priority": 100,
                "is_fallback": False,
            }
        }

        # Add fallback provider if configured
        fallback_provider = os.getenv("PEPPERPY_FALLBACK_PROVIDER")
        if fallback_provider:
            llm_config["fallback"] = {
                "type": fallback_provider,
                "model_name": os.getenv("PEPPERPY_FALLBACK_MODEL", "gpt-3.5-turbo"),
                "api_key": os.getenv("PEPPERPY_FALLBACK_API_KEY", ""),
                "priority": 50,
                "is_fallback": True,
            }

        # Initialize LLM manager
        await self.llm_manager.initialize(llm_config)

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.llm_manager.cleanup()
