"""
PepperPy Tool Result Module.

Result types for tool operations.
"""

from typing import Any, Dict, List, Optional


class ToolResult:
    """Result from tool execution."""
    
    def __init__(
        self, 
        success: bool, 
        data: Dict[str, Any], 
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize tool result.
        
        Args:
            success: Whether the operation was successful
            data: Result data
            error: Error message if unsuccessful
            metadata: Additional metadata
        """
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of the result
        """
        result = {
            "success": self.success,
            "data": self.data
        }
        
        if self.error:
            result["error"] = self.error
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        """Create from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Tool result instance
        """
        return cls(
            success=data.get("success", False),
            data=data.get("data", {}),
            error=data.get("error"),
            metadata=data.get("metadata")
        )
        
    def __repr__(self) -> str:
        """Get string representation.
        
        Returns:
            String representation
        """
        status = "success" if self.success else "error"
        error_info = f", error={self.error}" if self.error else ""
        return f"ToolResult(status={status}, data={self.data}{error_info})"
