"""
Base class for REST-based providers in PepperPy.

This module provides a base implementation for providers that interact with REST APIs,
handling common concerns like authentication, error handling, and retries.

Example:
    ```python
    from pepperpy.providers.rest_base import RESTProvider

    class MyAPIProvider(RESTProvider):
        def _get_default_base_url(self) -> str:
            return "https://api.example.com/v1"

        async def get_data(self, resource_id: str) -> Dict[str, Any]:
            response = await self._make_request(
                method="GET",
                endpoint=f"/resources/{resource_id}"
            )
            return response
    ```
"""

from typing import Any, Dict, Optional

import httpx

from pepperpy.core.errors import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from pepperpy.providers.base import BaseProvider
from pepperpy.utils.decorators import retry
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class RESTProvider(BaseProvider):
    """Base class for REST API-based providers.

    This class handles common concerns for providers that interact with REST APIs,
    such as authentication, error handling, retries, and connection management.

    Attributes:
        base_url: Base URL for the API
        api_key: Authentication key
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        client: HTTP client
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST provider.

        Args:
            name: Provider name
            api_key: Authentication key
            base_url: Base URL for the API (overrides default)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name=name, **kwargs)
        self.api_key = api_key
        self.base_url = base_url or self._get_default_base_url()
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = False  # Use a private attribute instead of property

    def _get_default_base_url(self) -> str:
        """Get the default base URL for this provider.

        Must be implemented by subclasses.

        Returns:
            Default base URL
        """
        raise NotImplementedError("Subclasses must implement _get_default_base_url")

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the HTTP client and validates the configuration.

        Raises:
            ProviderError: If initialization fails
        """
        if self.client is not None:
            await self.close()

        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
            # Optional validation request to check credentials
            await self._validate_credentials()
            self._initialized = True  # Use private attribute
        except Exception as e:
            raise ProviderError(
                f"Failed to initialize {self.name} provider: {str(e)}"
            ) from e

    async def _validate_credentials(self) -> None:
        """Validate API credentials.

        Can be overridden by subclasses to perform validation.

        Raises:
            AuthenticationError: If credentials are invalid
        """
        pass

    async def close(self) -> None:
        """Close the provider and release resources."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None
        self._initialized = False  # Use private attribute

    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers including authentication.

        Returns:
            Dict with headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PepperPy/1.0",
        }

    @retry(max_retries=3)
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make a request to the API with retries and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (will be appended to base_url)
            data: Request body data
            params: URL query parameters
            extra_headers: Additional headers to include
            timeout: Custom timeout for this request

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: When authentication fails
            NetworkError: When connection fails
            RateLimitError: When rate limit is exceeded
            ServerError: When server returns an error
            TimeoutError: When request times out
            ProviderError: For other errors
        """
        # Ensure client is initialized
        if not self.is_initialized or self.client is None:
            await self.initialize()

        # At this point, self.client should be initialized
        if self.client is None:
            raise ProviderError(
                f"Failed to initialize HTTP client for {self.name} provider"
            )

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        if extra_headers:
            headers.update(extra_headers)

        request_timeout = timeout or self.timeout

        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=request_timeout,
            )

            if response.status_code >= 200 and response.status_code < 300:
                return self._parse_response(response)
            else:
                await self._handle_error_response(response)
                # This line is never reached because _handle_error_response always raises an exception
                return {}  # Added to satisfy the linter

        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.name} API: {str(e)}") from e

        except httpx.ReadTimeout as e:
            raise TimeoutError(
                f"Request to {self.name} API timed out after {request_timeout}s"
            ) from e

        except httpx.HTTPStatusError as e:
            # This shouldn't happen as we handle status codes above
            raise ProviderError(f"HTTP error with {self.name} API: {str(e)}") from e

        except Exception as e:
            raise ProviderError(
                f"Error making request to {self.name} API: {str(e)}"
            ) from e

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse the API response into a standardized format.

        Args:
            response: HTTP response

        Returns:
            Parsed response data

        Raises:
            ProviderError: If response cannot be parsed
        """
        try:
            result: Dict[str, Any] = response.json()
            return result
        except Exception as e:
            raise ProviderError(
                f"Failed to parse {self.name} API response: {str(e)}"
            ) from e

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: HTTP response

        Raises:
            AuthenticationError: When authentication fails
            RateLimitError: When rate limit is exceeded
            ServerError: When server returns an error
            ProviderError: For other errors
        """
        try:
            error_data = response.json()
        except Exception:
            error_data = {}

        error_message = str(error_data.get("error", response.text or "Unknown error"))

        if response.status_code == 401:
            raise AuthenticationError(
                f"Authentication failed with {self.name} API: {error_message}"
            )
        elif response.status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded for {self.name} API: {error_message}"
            )
        elif response.status_code >= 500:
            raise ServerError(f"Server error from {self.name} API: {error_message}")
        else:
            raise ProviderError(
                f"{self.name} API error ({response.status_code}): {error_message}"
            )

    # Override the property from the parent class
    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized and self.client is not None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        return {
            "supports_async": True,
            "supports_streaming": False,  # Override in subclasses
            "supports_retries": True,
            "max_retries": self.max_retries,
        }
