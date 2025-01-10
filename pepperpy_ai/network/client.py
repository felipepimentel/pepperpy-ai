"""Network client implementation."""

from dataclasses import dataclass, field
from typing import Any, Optional, AsyncGenerator, TypeVar
from datetime import timedelta
import aiohttp
import backoff

from pepperpy_core.base import BaseData
from pepperpy_core.types import JsonDict
from ..exceptions import NetworkError

ResponseT = TypeVar("ResponseT")

@dataclass
class ClientConfig(BaseData):
    """Client configuration.
    
    Attributes:
        base_url: Base URL for requests
        name: Client name
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        headers: Default request headers
        metadata: Additional client metadata
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        retry_codes: HTTP status codes to retry on
    """
    # Required fields first
    base_url: str = ""
    name: str = ""  # From BaseData, must have default

    # Optional fields
    timeout: float = 30.0
    verify_ssl: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_codes: set[int] = field(default_factory=lambda: {408, 429, 500, 502, 503, 504})

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.base_url:
            raise ValueError("base_url cannot be empty")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")

class NetworkClient:
    """HTTP client with retry and error handling."""

    def __init__(self, config: ClientConfig) -> None:
        """Initialize client.
        
        Args:
            config: Client configuration
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "NetworkClient":
        """Enter async context."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        await self.disconnect()

    async def connect(self) -> None:
        """Create client session."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                headers=self.config.headers,
                timeout=timeout,
            )

    async def disconnect(self) -> None:
        """Close client session."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get client session.
        
        Raises:
            NetworkError: If client is not connected
        """
        if self._session is None:
            raise NetworkError("Client not connected")
        return self._session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, NetworkError),
        max_tries=lambda self: self.config.max_retries + 1,
        max_time=lambda self: self.config.timeout * (self.config.max_retries + 1),
    )
    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Send HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            NetworkError: If request fails
        """
        try:
            response = await self.session.request(method, url, **kwargs)
            if response.status in self.config.retry_codes:
                raise NetworkError(
                    f"Request failed with status {response.status}",
                    url=str(response.url),
                    method=method,
                    status_code=response.status,
                )
            return response
        except aiohttp.ClientError as e:
            raise NetworkError(
                str(e),
                url=url,
                method=method,
            ) from e

    async def get(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """Send GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """Send POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """Send PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """Send DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def stream(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> AsyncGenerator[bytes, None]:
        """Stream response data.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Yields:
            Response data chunks
            
        Raises:
            NetworkError: If request fails
        """
        async with await self.request(method, url, **kwargs) as response:
            async for chunk in response.content.iter_chunks():
                yield chunk[0]
