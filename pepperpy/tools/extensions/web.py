"""Web interaction tools."""

from typing import Any

import aiohttp

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import JSON, ToolResult


class HttpTool(Tool):
    """Tool for HTTP requests."""

    async def execute(self, data: dict[str, Any]) -> JSON:
        """Execute HTTP request.

        Args:
            data: Tool input data containing:
                - url: Target URL
                - method: HTTP method (GET, POST, etc.)
                - headers: Request headers (optional)
                - params: Query parameters (optional)
                - data: Request body (optional)
                - timeout: Request timeout (optional)

        Returns:
            JSON: Tool execution result containing:
                - success: Whether request was successful
                - status: HTTP status code
                - headers: Response headers
                - body: Response body
                - error: Error message if request failed
        """
        try:
            url = data.get("url")
            if not url:
                return ToolResult(
                    success=False,
                    data={},
                    error="URL is required",
                ).dict()

            method = data.get("method", "GET")
            headers = data.get("headers", {})
            params = data.get("params", {})
            body = data.get("data")
            timeout = data.get("timeout", 30)

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body,
                    timeout=timeout,
                ) as response:
                    return ToolResult(
                        success=True,
                        data={
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": await response.text(),
                        },
                    ).dict()

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
            ).dict()
