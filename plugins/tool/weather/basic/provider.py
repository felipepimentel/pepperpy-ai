"""Weather tool provider implementation."""

from typing import dict, list, Any

from pepperpy.tool import ToolProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.tool.base import ToolError
from pepperpy.tool.base import ToolError

logger = logger.getLogger(__name__)


class WeatherProvider(class WeatherProvider(ToolProvider, BasePluginProvider):
    """Provider for weather information."""):
    """
    Tool weather provider.
    
    This provider implements weather functionality for the PepperPy tool framework.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
 """
        if self.initialized:
            return

        # Get configuration values from self.config
        self.default_temperature = self.config.get("default_temperature", 22)
        self.default_condition = self.config.get("default_condition", "partly cloudy")
        self.use_static_data = self.config.get("use_static_data", True)

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

        self.logger.info("Weather tool initialized")

    async def cleanup(self) -> None:
 """Clean up resources.

        This method is called automatically when the context manager exits.
 """
        self.logger.info("Weather tool cleaned up")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a weather operation.

        Args:
            input_data: Task data containing:
                - task: Operation to perform (get_weather, get_forecast)
                - location: Location to get weather for
                - days: Number of days for forecast (optional)

        Returns:
            Operation result
        """
        if not self.initialized:
            await self.initialize()

        task = input_data.get("task")

        if not task:
            raise ToolError("No task specified")

        try:
            if task == "get_weather":
                location = input_data.get("location")

                if not location:
                    raise ToolError("No location provided")

                # Generate weather data
                if self.use_static_data:
                    weather = self._get_static_weather(location)
                else:
                    weather = self._get_random_weather(location)

                return {"status": "success", "location": location, "weather": weather}

            elif task == "get_forecast":
                location = input_data.get("location")
                days = input_data.get("days", 5)

                if not location:
                    raise ToolError("No location provided")

                if not isinstance(days, int) or days < 1 or days > 10:
                    raise ToolError("Days must be between 1 and 10",
                    )

                # Generate forecast data
                forecast = self._get_forecast(location, days)

                return {"status": "success", "location": location, "forecast": forecast}

            elif task == "get_capabilities":
                return {
                    "status": "success",
                    "capabilities": ["get_weather", "get_forecast"],
                }

            else:
                raise ToolError(f"Unknown task: {task)"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task}': {e}")
            return {"status": "error", "message": str(e)}

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
        import random

        return {
            "location": location,
            "temperature": random.randint(0, 35),
            "condition": random.choice(self.conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }

    def _get_forecast(self, location: str, days: int) -> list[dict[str, Any]]:
        """Get weather forecast for multiple days.

        Args:
            location: Location string
            days: Number of days for forecast

        Returns:
            list of daily forecasts
        """

        forecast = []

        for day in range(days):
            if self.use_static_data:
                daily = self._get_static_weather(location)
                daily["day"] = day + 1
            else:
                daily = self._get_random_weather(location)
                daily["day"] = day + 1

            forecast.append(daily)

        return forecast
