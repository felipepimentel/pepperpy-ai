"""
Stub MCP protocol definitions.

This module provides stub definitions for the core protocol for Model Context Protocol (MCP)
to be used when the original modules are not available.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MCPOperationType(str, Enum):
    """Operation types for MCP requests."""

    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CHAT = "chat"
    TOKENIZE = "tokenize"
    DETOKENIZE = "detokenize"


class MCPStatusCode(str, Enum):
    """Status codes for MCP responses."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class MCPRequest:
    """MCP request data."""

    request_id: str
    model_id: str
    operation: str | MCPOperationType  # Allow both str and MCPOperationType
    parameters: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        # Handle operation more flexibly
        if isinstance(self.operation, str):
            op_value = self.operation
        else:
            op_value = self.operation.value

        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "operation": op_value,  # Always use string form for serialization
            "parameters": self.parameters,
            "inputs": self.inputs,
        }


@dataclass
class MCPResponse:
    """MCP response data."""

    request_id: str
    model_id: str
    status: MCPStatusCode
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "status": self.status
            if isinstance(self.status, str)
            else self.status.value,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "error": self.error,
        }

    @classmethod
    def error_response(
        cls, request_id: str, model_id: str, error_message: str
    ) -> "MCPResponse":
        """Create an error response."""
        return cls(
            request_id=request_id,
            model_id=model_id,
            status=MCPStatusCode.ERROR,
            error=error_message,
        )
