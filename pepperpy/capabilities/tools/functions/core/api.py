"""Tool for making API requests."""

import asyncio
import json
import time
from typing import Any, Dict, Literal, Optional

import aiohttp
from pydantic import BaseModel

from ....tools.base import BaseTool, ToolConfig

Method = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


class APIResponse(BaseModel):
    """Response from API request."""

    status: int
    headers: Dict[str, str]
    body: Any
    elapsed: float


class APITool(BaseTool):
    """Tool for making API requests."""

    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        rate_limit: Optional[float] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize API tool.
        
        Args:
            name: Tool name
            base_url: Optional base URL for all requests
            headers: Optional default headers
            rate_limit: Optional minimum interval between requests in seconds
            config: Optional configuration
        """
        super().__init__(
            config=ToolConfig(
                name=name,
                description="Tool for making API requests",
                parameters=config or {},
            )
        )
        self.base_url = base_url
        self.headers = headers or {}
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session: Optional[aiohttp.ClientSession] = None

    async def _setup(self) -> None:
        """Set up tool resources."""
        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.headers
        )

    async def _teardown(self) -> None:
        """Clean up tool resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def request(
        self,
        method: Method,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Make an HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Optional request headers
            params: Optional query parameters
            json_data: Optional JSON body
            data: Optional form data
            
        Returns:
            API response
            
        Raises:
            Exception: If request fails
        """
        if not self.session:
            raise RuntimeError("Tool not initialized")
            
        # Handle rate limiting
        if self.rate_limit:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.rate_limit:
                wait_time = self.rate_limit - elapsed
                print(f"Rate limit hit, waiting {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
            self.last_request_time = time.time()
            
        # Merge headers
        request_headers = {**self.headers, **(headers or {})}
        
        # Make request
        start_time = time.time()
        async with self.session.request(
            method=method,
            url=url,
            headers=request_headers,
            params=params,
            json=json_data,
            data=data,
        ) as response:
            elapsed = time.time() - start_time
            
            # Get response body
            try:
                body = await response.json()
            except:
                body = await response.text()
                
            return APIResponse(
                status=response.status,
                headers=dict(response.headers),
                body=body,
                elapsed=elapsed
            )

    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Execute API request.
        
        Args:
            input_data: Request parameters
            context: Optional execution context
            
        Returns:
            API response
            
        Raises:
            ValueError: If parameters are invalid
        """
        method = str(input_data.get("method", "GET")).upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            raise ValueError(f"Invalid HTTP method: {method}")
            
        url = str(input_data.get("url", ""))
        if not url:
            raise ValueError("URL is required")
            
        response = await self.request(
            method=method,  # type: ignore
            url=url,
            headers=input_data.get("headers"),
            params=input_data.get("params"),
            json_data=input_data.get("json_data"),
            data=input_data.get("data"),
        )
        
        if response.status >= 300:
            raise ValueError(f"Request failed with status {response.status}")
            
        return response 