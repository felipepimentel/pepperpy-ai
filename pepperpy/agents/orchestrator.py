"""
Orchestrator agent for PepperPy.

The orchestrator is responsible for coordinating the actions of all agents
and plugins in the system, managing message routing and ensuring that the
right components are called at the right time.
"""

from typing import Any, Dict, Optional

from pepperpy.core.logging import get_logger
from pepperpy.plugins import PepperpyPlugin

logger = get_logger(__name__)


class Orchestrator:
    """
    Main orchestrator agent for PepperPy.

    The orchestrator is responsible for coordinating the flow of data and
    control between different agents and plugins.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the orchestrator.

        Args:
            config: Optional configuration for the orchestrator
        """
        self.config = config or {}
        self.plugins: Dict[str, PepperpyPlugin] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator and its plugins."""
        if self._initialized:
            return

        logger.info("Initializing orchestrator")
        self._initialized = True
        logger.info("Orchestrator initialized")

    async def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a query with context.

        Args:
            query: User query
            context: Context information

        Returns:
            Result of the query execution
        """
        if not self._initialized:
            await self.initialize()

        context = context or {}
        logger.info(f"Executing query: {query}")

        # Simply return the query for now
        return f"Processed query: {query}"

    async def cleanup(self) -> None:
        """Clean up orchestrator and plugins."""
        if not self._initialized:
            return

        logger.info("Cleaning up orchestrator")

        # Clean up all plugins
        for plugin_id, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                logger.info(f"Cleaned up plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_id}: {e}")

        self.plugins = {}
        self._initialized = False


# Singleton instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the singleton orchestrator instance.

    Returns:
        Orchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = Orchestrator()

    return _orchestrator
