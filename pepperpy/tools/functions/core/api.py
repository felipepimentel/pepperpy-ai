"""Tool for making API requests."""

import asyncio
import json
import time
from typing import Any, Dict, Literal, Optional

import aiohttp
from pydantic import BaseModel

from pepperpy.tools.tool import Tool, ToolResult


Method = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


class APIResponse(BaseModel):
    """Response from API request."""

    status: int
    headers: Dict[str, str]
    body: Any
    elapsed: float


class APITool(Tool):
    """Tool for making API requests."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        rate_limit: Optional[float] = None
    ) -> None:
        """Initialize API tool.
        
        Args:
            base_url: Optional base URL for all requests
            headers: Optional default headers
            rate_limit: Optional minimum interval between requests in seconds
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.headers
        )

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

    async def execute(self, **kwargs: Any) -> ToolResult[APIResponse]:
        """Execute API request.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Optional request headers
            params: Optional query parameters
            json_data: Optional JSON body
            data: Optional form data
            
        Returns:
            API response
        """
        method = str(kwargs.get("method", "GET")).upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            return ToolResult(
                success=False,
                error=f"Invalid HTTP method: {method}"
            )
            
        url = str(kwargs.get("url", ""))
        if not url:
            return ToolResult(
                success=False,
                error="URL is required"
            )
            
        try:
            response = await self.request(
                method=method,  # type: ignore
                url=url,
                headers=kwargs.get("headers"),
                params=kwargs.get("params"),
                json_data=kwargs.get("json_data"),
                data=kwargs.get("data"),
            )
            
            return ToolResult(
                success=200 <= response.status < 300,
                data=response,
                error=f"Request failed with status {response.status}" if response.status >= 300 else None
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None 