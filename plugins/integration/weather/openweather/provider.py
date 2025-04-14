"""OpenWeather API integration provider."""

import logging
from typing import Any
from urllib.parse import urljoin

import aiohttp

from pepperpy.core.base import PepperpyError
from pepperpy.plugin import ProviderPlugin


class IntegrationError(PepperpyError):
    """Base error for integration errors."""


class OpenWeatherProvider(ProviderPlugin):
    """Provider for OpenWeather API integration.

    This provider implements the OpenWeather API for weather data.
    """

    # Type-annotated config attributes
    api_key: str
    api_url: str = "https://api.openweathermap.org/data/2.5"
    timeout: int = 10
    units: str = "metric"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration."""
        super().__init__(**kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: aiohttp.ClientSession | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self._initialized:
            return

        if not self.api_key:
            raise IntegrationError("API key is required for OpenWeather API")

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        self._initialized = True
        self.logger.debug(
            f"Initialized OpenWeather API with timeout={self.timeout}, units={self.units}"
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False

    async def get_current_weather(self, location: str) -> dict[str, Any]:
        """Get current weather for a location.

        Args:
            location: City name or coordinates

        Returns:
            Weather data for the location
        """
        if not self._initialized:
            await self.initialize()

        try:
            endpoint = urljoin(self.api_url, "/weather")
            params = {"q": location, "appid": self.api_key, "units": self.units}

            if not self.session:
                raise IntegrationError("Session not initialized")

            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("message", "Unknown error")
                    raise IntegrationError(f"OpenWeather API error: {error_message}")

                data = await response.json()

                # Transform the response to our format
                return {
                    "location": location,
                    "temperature": data.get("main", {}).get("temp"),
                    "feels_like": data.get("main", {}).get("feels_like"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "pressure": data.get("main", {}).get("pressure"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "wind_direction": data.get("wind", {}).get("deg"),
                    "condition": data.get("weather", [{}])[0].get("main"),
                    "description": data.get("weather", [{}])[0].get("description"),
                    "icon": data.get("weather", [{}])[0].get("icon"),
                    "timestamp": data.get("dt"),
                }

        except aiohttp.ClientError as e:
            raise IntegrationError(f"Failed to connect to OpenWeather API: {e}") from e
        except Exception as e:
            raise IntegrationError(f"Error getting weather data: {e}") from e

    async def get_forecast(self, location: str, days: int = 5) -> dict[str, Any]:
        """Get weather forecast for a location.

        Args:
            location: City name or coordinates
            days: Number of days for forecast (max 5)

        Returns:
            Forecast data for the location
        """
        if not self._initialized:
            await self.initialize()

        try:
            endpoint = urljoin(self.api_url, "/forecast")
            params = {
                "q": location,
                "appid": self.api_key,
                "units": self.units,
                "cnt": min(
                    days * 8, 40
                ),  # API returns data in 3-hour intervals (8 per day)
            }

            if not self.session:
                raise IntegrationError("Session not initialized")

            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_message = error_data.get("message", "Unknown error")
                    raise IntegrationError(f"OpenWeather API error: {error_message}")

                data = await response.json()

                # Transform the response to our format
                forecast = []
                for item in data.get("list", []):
                    forecast.append(
                        {
                            "timestamp": item.get("dt"),
                            "temperature": item.get("main", {}).get("temp"),
                            "feels_like": item.get("main", {}).get("feels_like"),
                            "humidity": item.get("main", {}).get("humidity"),
                            "pressure": item.get("main", {}).get("pressure"),
                            "wind_speed": item.get("wind", {}).get("speed"),
                            "wind_direction": item.get("wind", {}).get("deg"),
                            "condition": item.get("weather", [{}])[0].get("main"),
                            "description": item.get("weather", [{}])[0].get(
                                "description"
                            ),
                            "icon": item.get("weather", [{}])[0].get("icon"),
                        }
                    )

                return {
                    "location": location,
                    "forecast": forecast,
                    "city": data.get("city", {}).get("name"),
                    "country": data.get("city", {}).get("country"),
                }

        except aiohttp.ClientError as e:
            raise IntegrationError(f"Failed to connect to OpenWeather API: {e}") from e
        except Exception as e:
            raise IntegrationError(f"Error getting forecast data: {e}") from e
