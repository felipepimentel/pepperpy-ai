"""
PepperPy Tool Results.

Result classes specific to tool operations.
"""

from typing import Any, Optional

from pepperpy.common.result import Result


class ToolResult(Result):
    """Result of a tool operation."""

    def __init__(
        self,
        content: Any,
        tool_name: str,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a tool result.

        Args:
            content: Tool output content
            tool_name: Name of the tool
            success: Whether the operation was successful
            error_message: Optional error message (if not successful)
            metadata: Optional metadata
            logger: Optional logger
        """
        metadata = metadata or {}
        metadata["tool_name"] = tool_name
        metadata["success"] = success
        if error_message:
            metadata["error"] = error_message

        super().__init__(content, metadata, logger)
        self.tool_name = tool_name
        self.success = success
        self.error_message = error_message

    @property
    def is_error(self) -> bool:
        """Check if the result represents an error.

        Returns:
            True if this is an error result
        """
        return not self.success


class APIResult(ToolResult):
    """Result of an API call."""

    def __init__(
        self,
        content: Any,
        tool_name: str,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize an API result.

        Args:
            content: API response content
            tool_name: Name of the API tool
            status_code: HTTP status code
            headers: Response headers
            success: Whether the call was successful
            error_message: Optional error message
            metadata: Optional metadata
            logger: Optional logger
        """
        metadata = metadata or {}
        if status_code is not None:
            metadata["status_code"] = status_code
        if headers:
            metadata["headers"] = headers

        super().__init__(content, tool_name, success, error_message, metadata, logger)
        self.status_code = status_code
        self.headers = headers or {}
