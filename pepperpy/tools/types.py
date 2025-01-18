"""Type definitions for tools."""

from typing import Any

from pydantic import BaseModel, Field

# JSON type alias
JSON = dict[str, Any] | list[Any] | str | int | float | bool | None


class ToolConfig(BaseModel):
    """Tool configuration."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(..., description="Tool parameters")
    required_parameters: list[str] = Field(
        default_factory=list, description="Required parameters"
    )
    optional_parameters: list[str] = Field(
        default_factory=list, description="Optional parameters"
    )
    examples: list[dict[str, Any]] = Field(
        default_factory=list, description="Example usages"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ToolInput(BaseModel):
    """Tool input data."""

    tool_name: str = Field(..., description="Tool name")
    parameters: dict[str, Any] = Field(..., description="Tool parameters")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ToolResult(BaseModel):
    """Tool execution result."""

    success: bool = Field(..., description="Whether tool execution was successful")
    data: JSON = Field(..., description="Tool execution result data")
    error: str | None = Field(None, description="Error message if execution failed")
