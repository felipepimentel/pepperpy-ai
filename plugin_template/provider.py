"""Template provider implementation for PepperPy plugin.

This template demonstrates the correct implementation pattern for
PepperPy plugins following the implementation guide.
"""

from typing import Any

from pepperpy.domain.base import DomainInterface
from pepperpy.plugin.provider import BasePluginProvider


class TemplateProvider(DomainInterface, BasePluginProvider):
    """Template provider implementation for Domain.

    This class demonstrates the correct implementation pattern for PepperPy plugins.
    Always inherit from both the domain interface and BasePluginProvider.
    """

    async def initialize(self) -> None:
        """Initialize provider resources.

        Always call super().initialize() first to set up base class resources.
        Never initialize resources in __init__, use this method instead.
        Use self.config.get() for accessing configuration values.
        """
        # Initialize base class first
        await super().initialize()

        if self.initialized:
            return

        # Log initialization with configuration (never log sensitive data)
        self.logger.debug(
            f"Initializing {self.__class__.__name__} with "
            f"model={self.config.get('model', 'default')}"
        )

        # Initialize any resources needed by the provider
        self.client = None
        try:
            # Example resource initialization
            api_key = self.config.get("api_key")
            if not api_key:
                self.logger.warning("No API key provided, using environment variable")

            # self.client = Client(api_key=api_key)
            # Additional initialization...

        except Exception as e:
            self.logger.error(f"Error initializing provider: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up provider resources.

        Always release all resources created during initialization.
        Call super().cleanup() last to clean up base class resources.
        """
        try:
            # Clean up provider-specific resources
            if hasattr(self, "client") and self.client:
                # await self.client.close()
                self.client = None

            self.logger.debug(f"Cleaned up {self.__class__.__name__} resources")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        finally:
            # Always call base class cleanup last
            await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Dictionary containing task and parameters

        Returns:
            Dictionary with execution results

        Raises:
            DomainError: If execution fails
        """
        # Extract task type
        task_type = input_data.get("task")
        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Initialize if not already initialized
            if not self.initialized:
                await self.initialize()

            # Process different task types
            if task_type == "task_one":
                result = await self._process_task_one(input_data)
            elif task_type == "task_two":
                result = await self._process_task_two(input_data)
            else:
                return {"status": "error", "error": f"Unknown task: {task_type}"}

            return {"status": "success", "result": result}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    # Domain-specific methods

    async def domain_specific_method(self, param: str) -> str:
        """Example domain-specific method.

        Args:
            param: Input parameter

        Returns:
            Result string
        """
        # Example of accessing other services through helper methods
        # llm_provider = self.llm()
        # memory = self.memory()

        # Domain-specific implementation
        return f"Processed: {param}"

    # Private helper methods

    async def _process_task_one(self, input_data: dict[str, Any]) -> Any:
        """Process task one.

        Args:
            input_data: Task input data

        Returns:
            Task result
        """
        # Implementation details
        param = input_data.get("param", "default")
        return await self.domain_specific_method(param)

    async def _process_task_two(self, input_data: dict[str, Any]) -> Any:
        """Process task two.

        Args:
            input_data: Task input data

        Returns:
            Task result
        """
        # Implementation details
        param = input_data.get("param", "default")
        return f"Task two result: {param}"
