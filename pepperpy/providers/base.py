"""Classes base para provedores.

Este módulo define interfaces comuns para todos os provedores,
incluindo a implementação base para provedores REST e outros tipos de provedores.

Example:
    ```python
    # Basic provider
    from pepperpy.providers.base import Provider

    class MyCustomProvider(Provider):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Custom initialization

        def connect(self):
            # Custom connection logic
            pass

    # REST provider
    from pepperpy.providers.base import RESTProvider

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

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, TypeVar, cast

import httpx

from pepperpy.core.errors import (
    AuthenticationError,
    NetworkError,
    PepperPyError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from pepperpy.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")

# Provider base classes and interfaces


class Provider(Protocol):
    """Base protocol for all providers.

    This protocol defines the minimum interface that all providers must implement.
    """

    name: str

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this provider.

        Returns:
            Dict[str, Any]: A dictionary of capabilities.
        """
        ...


class AsyncProvider(Provider, Protocol):
    """Protocol for providers that support async operations.

    This protocol defines the interface for providers that support asynchronous
    operations.
    """

    async def initialize(self) -> None:
        """Initialize the provider asynchronously.

        This method should be called before using the provider.
        """
        ...

    async def close(self) -> None:
        """Close the provider and release any resources.

        This method should be called when the provider is no longer needed.
        """
        ...


class StorageProvider(Provider, Protocol):
    """Protocol for storage providers.

    This protocol defines the interface for providers that offer storage
    capabilities.
    """

    async def save(self, key: str, data: Any) -> None:
        """Save data to storage.

        Args:
            key: The key to store the data under.
            data: The data to store.
        """
        ...

    async def load(self, key: str) -> Any:
        """Load data from storage.

        Args:
            key: The key to load the data from.

        Returns:
            The loaded data.
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: The key to delete.
        """
        ...


# Error classes


class ProviderError(PepperPyError):
    """Base class for provider errors."""

    pass


# Custom RateLimitError with retry_after support
class CustomRateLimitError(RateLimitError):
    """Rate limit error with retry-after information."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


# REST provider implementation


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retry_on: Optional[List[Type[Exception]]] = None,
):
    """Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retries before giving up.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff_factor: Backoff multiplier.
        retry_on: List of exception types to retry on.
            Defaults to [NetworkError, ServerError, TimeoutError, RateLimitError].

    Returns:
        The decorated function.
    """
    if retry_on is None:
        retry_on = [
            NetworkError,
            ServerError,
            TimeoutError,
            RateLimitError,
            CustomRateLimitError,
        ]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(retry_on) as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    if (
                        isinstance(e, CustomRateLimitError)
                        and hasattr(e, "retry_after")
                        and e.retry_after is not None
                    ):
                        # Use the retry-after header if available
                        wait_time = e.retry_after
                    else:
                        wait_time = min(delay, max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed with error: {str(e)}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )

                    await asyncio.sleep(wait_time)
                    delay = min(delay * backoff_factor, max_delay)
                except Exception as e:
                    # Don't retry on other exceptions
                    raise e

            if last_exception:
                raise last_exception
            return None  # This should never happen

        return wrapper

    return decorator


class BaseProvider:
    """Base class for all providers.

    This class provides common functionality for all providers, such as
    configuration management and capability reporting.
    """

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider.

        Args:
            name: The name of the provider.
            **kwargs: Additional provider-specific configuration.
        """
        self.name = name
        self.config = kwargs
        self._initialized = False

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this provider.

        Returns:
            Dict[str, Any]: A dictionary of capabilities.
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
        }

    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            bool: True if the provider is initialized, False otherwise.
        """
        return self._initialized


class RESTProvider(BaseProvider):
    """Base class for REST API providers.

    This class provides common functionality for interacting with REST APIs,
    such as authentication, request handling, and error management.
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
        """Initialize the REST provider.

        Args:
            name: The name of the provider.
            api_key: The API key for authentication.
            base_url: The base URL for the API. If None, uses the default from _get_default_base_url.
            timeout: The timeout for API requests in seconds.
            max_retries: The maximum number of retries for failed requests.
            **kwargs: Additional provider-specific configuration.
        """
        super().__init__(name=name, **kwargs)
        self.api_key = api_key
        self.base_url = base_url or self._get_default_base_url()
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False

    def _get_default_base_url(self) -> str:
        """Get the default base URL for the API.

        This method should be overridden by subclasses to provide a default base URL.

        Returns:
            str: The default base URL.
        """
        raise NotImplementedError(
            "Subclasses must implement _get_default_base_url method"
        )

    async def initialize(self) -> None:
        """Initialize the provider.

        This method creates the HTTP client and validates credentials if needed.
        It should be called before using the provider.
        """
        if self._initialized:
            return

        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            base_url=self.base_url,
            headers=self._get_headers(),
        )

        try:
            await self._validate_credentials()
            self._initialized = True
        except Exception as e:
            await self.close()
            raise e

    async def _validate_credentials(self) -> None:
        """Validate the provider credentials.

        This method should be overridden by subclasses to validate credentials
        if needed. The default implementation does nothing.
        """
        pass  # Default implementation does nothing

    async def close(self) -> None:
        """Close the provider and release any resources.

        This method should be called when the provider is no longer needed.
        """
        if self._client:
            await self._client.aclose()
            self._client = None
        self._initialized = False

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests.

        This method should be overridden by subclasses to provide the appropriate
        headers for authentication and other requirements.

        Returns:
            Dict[str, str]: The headers for API requests.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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
        """Make an HTTP request to the API.

        Args:
            method: The HTTP method (GET, POST, etc.).
            endpoint: The API endpoint.
            data: The request data (for POST, PUT, etc.).
            params: The query parameters.
            extra_headers: Additional headers to include.
            timeout: The timeout for this specific request.

        Returns:
            Dict[str, Any]: The parsed response JSON.

        Raises:
            AuthenticationError: If authentication fails.
            NetworkError: If a network error occurs.
            ServerError: If the server returns an error status.
            TimeoutError: If the request times out.
            ProviderError: For other provider-specific errors.
        """
        if not self._initialized or not self._client:
            await self.initialize()

        if not self._client:
            raise ProviderError("Failed to initialize provider client")

        # Build request headers
        headers = self._get_headers()
        if extra_headers:
            headers.update(extra_headers)

        # Configure timeout
        request_timeout = timeout or self.timeout

        # Convert data to JSON if present
        json_data = data if data is not None else None

        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers,
                timeout=request_timeout,
            )

            # Check for error responses
            if response.status_code >= 400:
                await self._handle_error_response(response)

            # Parse the successful response
            return self._parse_response(response)

        except httpx.TimeoutException as e:
            error_msg = f"Request timed out after {request_timeout} seconds: {str(e)}"
            logger.error(error_msg)
            raise TimeoutError(error_msg) from e
        except httpx.NetworkError as e:
            error_msg = f"Network error occurred: {str(e)}"
            logger.error(error_msg)
            raise NetworkError(error_msg) from e
        except httpx.HTTPStatusError as e:
            # This should be handled by _handle_error_response, but just in case
            error_msg = f"HTTP error occurred: {str(e)}"
            logger.error(error_msg)
            raise ServerError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during API request: {str(e)}"
            logger.error(error_msg)
            raise ProviderError(error_msg) from e

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse the API response.

        This method parses the response JSON and returns it. It can be overridden
        by subclasses to implement custom response parsing.

        Args:
            response: The HTTP response.

        Returns:
            Dict[str, Any]: The parsed response data.

        Raises:
            ProviderError: If the response cannot be parsed.
        """
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                return cast(Dict[str, Any], response.json())
            else:
                # Return a simple dict with the text content for non-JSON responses
                return {"content": response.text}
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            logger.error(error_msg)
            raise ProviderError(error_msg) from e

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        This method raises the appropriate exception based on the error response.
        It can be overridden by subclasses to implement custom error handling.

        Args:
            response: The HTTP response with an error status code.

        Raises:
            AuthenticationError: For authentication errors (401, 403).
            CustomRateLimitError: For rate limit errors (429).
            ServerError: For server errors (500+).
            ProviderError: For other API errors.
        """
        status_code = response.status_code
        error_msg = f"API error {status_code}"

        # Try to extract error details from response
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                error_detail = error_data.get("error", {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get("message", error_msg)
                elif isinstance(error_detail, str):
                    error_msg = error_detail
        except (json.JSONDecodeError, KeyError):
            # If we can't parse the JSON or find the error message, use the text
            error_msg = f"{error_msg}: {response.text[:100]}"

        # Map status codes to appropriate exceptions
        if status_code in (401, 403):
            raise AuthenticationError(f"Authentication failed: {error_msg}")
        elif status_code == 429:
            # Check for retry-after header
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    retry_seconds = int(retry_after)
                except ValueError:
                    # If it's a date, we'd need to parse it, but for simplicity
                    # we'll just use a default
                    retry_seconds = 60
            else:
                retry_seconds = 60

            raise CustomRateLimitError(
                f"Rate limit exceeded: {error_msg}", retry_after=retry_seconds
            )
        elif status_code >= 500:
            raise ServerError(f"Server error: {error_msg}")
        else:
            raise ProviderError(f"API error: {error_msg}")

    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            bool: True if the provider is initialized, False otherwise.
        """
        return self._initialized

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this provider.

        Returns:
            Dict[str, Any]: A dictionary of capabilities.
        """
        capabilities = super().get_capabilities()
        capabilities.update({
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        })
        return capabilities


# Export all classes
__all__ = [
    # Base provider classes
    "Provider",
    "AsyncProvider",
    "BaseProvider",
    "RESTProvider",
    "StorageProvider",
    # Error classes
    "ProviderError",
    "AuthenticationError",
    "NetworkError",
    "RateLimitError",
    "CustomRateLimitError",
    "ServerError",
    "TimeoutError",
    # Utility functions
    "retry",
]
