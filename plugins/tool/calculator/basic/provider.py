"""Calculator tool provider implementation."""

from typing import Any

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.tool.base import ToolProvider
from plugins.workflow.ai_gateway.gateway import GatewayRequest, GatewayResponse


class CalculatorProvider(ToolProvider, BasePluginProvider):
    """Provider for evaluating mathematical expressions.

    This tool provides basic calculation capabilities for mathematical expressions.
    """

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Initialize state
        self.initialized = True

        # Initialize configuration
        self.allow_complex = self.config.get("allow_complex", False)
        self.max_digits = self.config.get("max_digits", 10)

        self.logger.debug(
            f"Calculator initialized with allow_complex={self.allow_complex}, max_digits={self.max_digits}"
        )

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        # No resources to clean up
        self.initialized = False

    def get_tool_id(self) -> str:
        """Get the tool identifier."""
        return "calculator"

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a calculator operation.

        Args:
            input_data: Input data containing expression to evaluate

        Returns:
            Calculation result
        """
        # Get expression from input
        expression = input_data.get("expression", "")

        if not expression:
            return {"status": "error", "error": "No expression provided"}

        try:
            # Use safer eval with limited scope
            # In a real implementation, use a proper math parser
            allowed_names = {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
            }

            # Add additional functions if complex calculations are allowed
            if self.allow_complex:
                import math

                allowed_names.update(
                    {
                        "sin": math.sin,
                        "cos": math.cos,
                        "tan": math.tan,
                        "sqrt": math.sqrt,
                        "log": math.log,
                        "log10": math.log10,
                        "pi": math.pi,
                        "e": math.e,
                    }
                )

            # Evaluate expression with limited scope
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            # Format result according to configuration
            if isinstance(result, (int, float)):
                formatted_result = f"{result:.{self.max_digits}g}"
            else:
                formatted_result = str(result)

            return {"status": "success", "result": formatted_result}

        except Exception as e:
            self.logger.error(f"Error calculating expression '{expression}': {e}")
            return {"status": "error", "error": f"Calculation error: {e!s}"}

    async def handle_gateway_request(self, request: GatewayRequest) -> GatewayResponse:
        """Handle a gateway request.

        Args:
            request: Gateway request with expression to evaluate

        Returns:
            Gateway response with calculation result
        """
        # Extract input from gateway request
        input_data = {"expression": request.inputs.get("expression", "")}

        # Execute the calculation
        result = await self.execute(input_data)

        # Convert to gateway response
        if result.get("status") == "success":
            return GatewayResponse.success(
                request.request_id, {"result": result.get("result")}
            )
        else:
            return GatewayResponse.error(
                request.request_id, result.get("error", "Unknown error")
            )
