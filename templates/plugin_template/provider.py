"""Provider implementation for domain."""

import logging
from typing import Any

# Import domain interface and plugin base class
from pepperpy.domain import DomainProvider
from pepperpy.domain.errors import DomainError
from pepperpy.plugin.provider import BasePluginProvider

# Get domain-specific logger
logger = logging.getLogger(__name__)


class ProviderClass(DomainProvider, BasePluginProvider):
    """Provider implementation for domain.

    This class implements the domain provider interface for specific functionality.

    Attributes:
        option1: First configuration option
        option2: Second configuration option
        array_option: List configuration option
    """

    # Type-annotated config attributes for direct access
    option1: str
    option2: int
    array_option: list[str]

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize provider with configuration.

        Args:
            config: Configuration dictionary
            **kwargs: Additional configuration options
        """
        super().__init__()

        # Merge config and kwargs
        config_data = config or {}
        config_data.update(kwargs)

        # Set configuration options with defaults
        self.option1 = config_data.get("option1", "default_value")
        self.option2 = config_data.get("option2", 42)
        self.array_option = config_data.get("array_option", ["value1", "value2"])

        # Initialize operational state
        self._client = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize provider resources.

        ALWAYS check initialization flag first.
        NEVER initialize in constructor.
        """
        if self.initialized:
            return

        try:
            # Initialize resources
            logger.debug(
                f"Initializing {self.__class__.__name__} with option1={self.option1}"
            )
            self._client = await self._create_client()
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
            raise DomainError(f"Provider initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        ALWAYS release all resources.
        """
        if not self.initialized:
            return

        try:
            # Clean up resources
            if self._client:
                await self._client.close()
                self._client = None
            self.initialized = False
            logger.debug(f"Cleaned up {self.__class__.__name__} resources")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def _create_client(self) -> Any:
        """Create client for external service.

        Returns:
            Client instance
        """
        # Example client creation
        return {"connection": "established"}

    async def process(self, input_data: str) -> str:
        """Process input data.

        This method should be implemented according to the domain interface.

        Args:
            input_data: Input data to process

        Returns:
            Processed output

        Raises:
            DomainError: If processing fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Process input data using client
            logger.debug(f"Processing input: {input_data[:50]}...")
            return f"Processed: {input_data} (with option1={self.option1})"
        except Exception as e:
            raise DomainError(f"Processing failed: {e}") from e

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Common plugin interface method for executing tasks.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Initialize if needed
            if not self.initialized:
                await self.initialize()

            # Dispatch to appropriate handler based on task
            if task_type == "process":
                # Extract parameters
                text = input_data.get("text")
                if not text:
                    return {"status": "error", "error": "No text provided"}

                # Process text
                result = await self.process(text)

                # Return success result
                return {
                    "status": "success",
                    "result": result,
                }

            elif task_type == "another_task":
                # Handle another task type
                return {
                    "status": "success",
                    "message": "Another task executed",
                }

            else:
                # Unknown task
                return {"status": "error", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            # Log and return error
            logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    @property
    def name(self) -> str:
        """Get provider name."""
        return "provider_name"

    @property
    def capabilities(self) -> dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of capabilities
        """
        return {
            "feature1": True,
            "feature2": True,
            "options": {
                "option1": self.option1,
                "option2": self.option2,
            },
        }
