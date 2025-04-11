"""Weather tool provider implementation."""

import logging
import random
from typing import Any

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.tool.base import ToolProvider
from plugins.workflow.ai_gateway.gateway import GatewayRequest, GatewayResponse


class WeatherProvider(ToolProvider, BasePluginProvider):
    """Provider for weather information.

    ALWAYS inherit from both domain provider and BasePluginProvider.
    """

    default_temperature: int = 22
    default_condition: str = "partly cloudy"
    use_static_data: bool = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration.

        Args:
            **kwargs: Configuration parameters
        """
        super().__init__(**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialized = False

        # Weather conditions for random generation
        self.conditions = [
            "sunny",
            "partly cloudy",
            "cloudy",
            "rainy",
            "stormy",
            "snowy",
            "foggy",
            "windy",
        ]

    async def initialize(self) -> None:
        """Initialize provider resources.

        ALWAYS check initialization flag.
        NEVER initialize in constructor.
        """
        if self.initialized:
            return

        self.logger.info("Weather tool initialized")
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False
        self.logger.info("Weather tool cleaned up")

    def get_tool_id(self) -> str:
        """Get the tool identifier."""
        return "weather"

    async def execute(self, request: GatewayRequest) -> GatewayResponse:
        """Provide weather information.

        Args:
            request: Gateway request with location

        Returns:
            Gateway response with weather data
        """
        if not self.initialized:
            return GatewayResponse.error(request.request_id, "Provider not initialized")

        try:
            location = request.inputs.get("location", "")

            if not location:
                return GatewayResponse.error(request.request_id, "No location provided")

            # Generate weather data
            if self.use_static_data:
                weather = self._get_static_weather(location)
            else:
                weather = self._get_random_weather(location)

            return GatewayResponse.success(request.request_id, {"weather": weather})
        except Exception as e:
            self.logger.error(f"Error getting weather: {e}")
            return GatewayResponse.error(request.request_id, f"Weather error: {e!s}")

    def _get_static_weather(self, location: str) -> dict[str, Any]:
        """Get static weather data.

        Args:
            location: Location string

        Returns:
            Weather data dictionary
        """
        return {
            "location": location,
            "temperature": self.default_temperature,
            "condition": self.default_condition,
            "humidity": 65,
            "wind_speed": 10,
        }

    def _get_random_weather(self, location: str) -> dict[str, Any]:
        """Get randomized weather data.

        Args:
            location: Location string

        Returns:
            Weather data dictionary
        """
        return {
            "location": location,
            "temperature": random.randint(0, 35),
            "condition": random.choice(self.conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }
