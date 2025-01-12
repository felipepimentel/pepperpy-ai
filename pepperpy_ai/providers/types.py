"""Provider types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, TypedDict, Optional, cast

from ..types import JsonDict, Serializable
from ..exceptions import ValidationError


def safe_str(value: Any, default: str = "") -> str:
    """Safely convert value to string."""
    return str(value) if value is not None else default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to bool."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default

def safe_str_or_none(value: Any) -> Optional[str]:
    """Safely convert value to string or None."""
    return str(value) if value is not None else None

class ProviderType(str, Enum):
    """Provider types.
    
    Supported AI provider types.
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    STACKSPOT = "stackspot"

    @classmethod
    def from_str(cls, value: str) -> "ProviderType":
        """Create from string.
        
        Args:
            value: Provider type string
            
        Returns:
            Provider type
            
        Raises:
            ValueError: If value is invalid
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid provider type: {value}. "
                f"Supported types: {', '.join(cls.__members__.keys())}"
            )

class CapabilitiesDict(TypedDict, total=False):
    """Type definition for capabilities dictionary."""

    streaming: bool
    embeddings: bool
    functions: bool
    max_tokens: int
    max_requests_per_minute: int
    supports_batch: bool
    batch_size: int

@dataclass
class ProviderCapabilities:
    """Provider capabilities."""

    streaming: bool = False
    embeddings: bool = False
    functions: bool = False
    max_tokens: int = 0
    max_requests_per_minute: int = 0
    supports_batch: bool = False
    batch_size: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderCapabilities":
        """Create capabilities from dictionary."""
        caps = data.get("capabilities", {})
        if not isinstance(caps, dict):
            caps = {}
        
        return cls(
            streaming=safe_bool(caps.get("streaming")),
            embeddings=safe_bool(caps.get("embeddings")),
            functions=safe_bool(caps.get("functions")),
            max_tokens=safe_int(caps.get("max_tokens")),
            max_requests_per_minute=safe_int(caps.get("max_requests_per_minute")),
            supports_batch=safe_bool(caps.get("supports_batch")),
            batch_size=safe_int(caps.get("batch_size"), 1),
        )

@dataclass
class ProviderMetadata(Serializable):
    """Provider metadata.
    
    Attributes:
        name: Provider name
        version: Provider version
        description: Provider description
        settings: Provider settings
        capabilities: Provider capabilities
        created_at: Creation timestamp
        updated_at: Update timestamp
    """
    name: str
    version: str
    description: Optional[str] = None
    settings: JsonDict = field(default_factory=dict)
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "settings": self.settings,
            "capabilities": {
                "streaming": self.capabilities.streaming,
                "embeddings": self.capabilities.embeddings,
                "functions": self.capabilities.functions,
                "max_tokens": self.capabilities.max_tokens,
                "max_requests_per_minute": self.capabilities.max_requests_per_minute,
                "supports_batch": self.capabilities.supports_batch,
                "batch_size": self.capabilities.batch_size,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ProviderMetadata":
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                message="Data must be a dictionary",
                field="data",
                value=str(data)
            )
            
        name = safe_str(data.get("name"))
        if not name:
            raise ValidationError(
                message="Name is required",
                field="name",
                value=str(data.get("name"))
            )
            
        version = safe_str(data.get("version"))
        if not version:
            raise ValidationError(
                message="Version is required",
                field="version",
                value=str(data.get("version"))
            )

        settings = data.get("settings", {})
        if not isinstance(settings, dict):
            settings = {}

        description = safe_str_or_none(data.get("description"))

        return cls(
            name=name,
            version=version,
            description=description,
            settings=cast(JsonDict, settings),
            capabilities=ProviderCapabilities.from_dict(data),
            created_at=datetime.fromisoformat(
                safe_str(data.get("created_at"), datetime.now().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                safe_str(data.get("updated_at"), datetime.now().isoformat())
            ),
        )

@dataclass
class ProviderResponse(Serializable):
    """Provider response.
    
    Attributes:
        content: Response content
        metadata: Response metadata
        raw_response: Raw provider response
        created_at: Creation timestamp
        tokens_used: Number of tokens used
        finish_reason: Reason for completion
    """
    content: str
    metadata: JsonDict = field(default_factory=dict)
    raw_response: Any | None = None
    created_at: datetime = field(default_factory=datetime.now)
    tokens_used: int = 0
    finish_reason: Optional[str] = None

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ProviderResponse":
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(
                message="Data must be a dictionary",
                field="data",
                value=str(data)
            )
            
        content = safe_str(data.get("content", ""))
        if not content:
            raise ValidationError(
                message="Content is required",
                field="content",
                value=str(data.get("content"))
            )

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return cls(
            content=content,
            metadata=cast(JsonDict, metadata),
            created_at=datetime.fromisoformat(
                safe_str(data.get("created_at", datetime.now().isoformat()))
            ),
            tokens_used=safe_int(data.get("tokens_used")),
            finish_reason=safe_str_or_none(data.get("finish_reason")),
        )

@dataclass
class ProviderUsage:
    """Provider usage statistics.
    
    Attributes:
        total_tokens: Total tokens used
        total_requests: Total requests made
        total_errors: Total errors encountered
        average_latency: Average request latency
        requests_per_minute: Current requests per minute
        last_request: Last request timestamp
    """
    total_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    average_latency: float = 0.0
    requests_per_minute: float = 0.0
    last_request: datetime | None = None

    def update(
        self,
        tokens: int = 0,
        latency: float = 0.0,
        error: bool = False
    ) -> None:
        """Update usage statistics.
        
        Args:
            tokens: Tokens used
            latency: Request latency
            error: Whether request resulted in error
        """
        now = datetime.now()
        self.total_tokens += tokens
        self.total_requests += 1
        if error:
            self.total_errors += 1

        # Update average latency
        if self.total_requests > 1:
            self.average_latency = (
                (self.average_latency * (self.total_requests - 1) + latency)
                / self.total_requests
            )
        else:
            self.average_latency = latency

        # Update requests per minute
        if self.last_request:
            time_diff = (now - self.last_request).total_seconds() / 60
            if time_diff > 0:
                self.requests_per_minute = 1 / time_diff

        self.last_request = now

@dataclass
class ProviderError(Exception):
    """Provider error.
    
    Attributes:
        message: Error message
        code: Error code
        details: Error details
        cause: Original exception
        timestamp: Error timestamp
    """
    message: str
    code: str | None = None
    details: JsonDict = field(default_factory=dict)
    cause: Exception | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        """Get string representation."""
        parts = [self.message]
        if self.code:
            parts.append(f"(code: {self.code})")
        if self.details:
            parts.append(f"details: {self.details}")
        if self.cause:
            parts.append(f"caused by: {self.cause!s}")
        return " ".join(parts)

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }
