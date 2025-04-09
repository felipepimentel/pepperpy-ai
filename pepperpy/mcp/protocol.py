"""
MCP protocol definitions.

This module defines the core protocol for Model Context Protocol (MCP).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

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
    operation: MCPOperationType
    parameters: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "operation": self.operation if isinstance(self.operation, str) else self.operation.value,
            "parameters": self.parameters,
            "inputs": self.inputs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        """Create from dictionary."""
        # Convert string operation to enum
        if isinstance(data.get("operation"), str):
            try:
                data["operation"] = MCPOperationType(data["operation"])
            except ValueError:
                # Use COMPLETION as default if invalid
                data["operation"] = MCPOperationType.COMPLETION
        
        return cls(
            request_id=data.get("request_id", ""),
            model_id=data.get("model_id", ""),
            operation=data.get("operation", MCPOperationType.COMPLETION),
            parameters=data.get("parameters", {}),
            inputs=data.get("inputs", {})
        )
    
@dataclass
class MCPResponse:
    """MCP response data."""
    request_id: str
    model_id: str
    status: MCPStatusCode
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "status": self.status if isinstance(self.status, str) else self.status.value,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResponse":
        """Create from dictionary."""
        # Convert string status to enum
        if isinstance(data.get("status"), str):
            try:
                data["status"] = MCPStatusCode(data["status"])
            except ValueError:
                # Use ERROR as default if invalid
                data["status"] = MCPStatusCode.ERROR
        
        return cls(
            request_id=data.get("request_id", ""),
            model_id=data.get("model_id", ""),
            status=data.get("status", MCPStatusCode.ERROR),
            outputs=data.get("outputs", {}),
            metadata=data.get("metadata", {}),
            error=data.get("error", "")
        )
    
    @classmethod
    def error_response(cls, request_id: str, model_id: str, error_message: str) -> "MCPResponse":
        """Create an error response."""
        return cls(
            request_id=request_id,
            model_id=model_id,
            status=MCPStatusCode.ERROR,
            error=error_message
        ) 