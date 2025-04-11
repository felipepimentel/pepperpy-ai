"""Calculator tool provider implementation."""

import logging
from typing import Any, Dict

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.tool.base import ToolProvider
from plugins.workflow.ai_gateway.gateway import GatewayRequest, GatewayResponse


class CalculatorProvider(ToolProvider, BasePluginProvider):
    """Provider for evaluating mathematical expressions.

    ALWAYS inherit from both domain provider and ProviderPlugin.
    """

    allow_complex: bool = False
    max_digits: int = 10

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration.

        Args:
            **kwargs: Configuration parameters
        """
        super().__init__(**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize provider resources.

        ALWAYS check initialization flag.
        NEVER initialize in constructor.
        """
        if self.initialized:
            return

        self.logger.info("Calculator tool initialized")
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False
        self.logger.info("Calculator tool cleaned up")

    def get_tool_id(self) -> str:
        """Get the tool identifier."""
        return "calculator"

    async def execute(self, request: GatewayRequest) -> GatewayResponse:
        """Evaluate a mathematical expression.

        Args:
            request: Gateway request with expression to evaluate

        Returns:
            Gateway response with calculation result
        """
        if not self.initialized:
            return GatewayResponse.error(request.request_id, "Provider not initialized")

        try:
            expression = request.inputs.get("expression", "")

            if not expression:
                return GatewayResponse.error(
                    request.request_id, "No expression provided"
                )

            # Use safer eval with limited scope
            # In a real implementation, use a proper math parser
            allowed_names = {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
            }

            # Evaluate expression with limited scope
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            # Format result according to configuration
            if isinstance(result, (int, float)):
                formatted_result = f"{result:.{self.max_digits}g}"
            else:
                formatted_result = str(result)

            return GatewayResponse.success(
                request.request_id, {"result": formatted_result}
            )
        except Exception as e:
            self.logger.error(f"Error calculating: {e}")
            return GatewayResponse.error(
                request.request_id, f"Calculation error: {e!s}"
            )
