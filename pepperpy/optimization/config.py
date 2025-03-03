"""Configuration settings for optimization components."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BatchingConfig(BaseModel):
    """Configuration for request batching."""

    max_batch_size: int = Field(default=32, ge=1, description="Maximum items per batch")
    max_wait_time: float = Field(
        default=0.5,
        ge=0.0,
        description="Maximum time to wait for batch completion in seconds",
    )
    min_batch_size: int = Field(
        default=1,
        ge=1,
        description="Minimum items required to process batch",
    )
    priority_levels: int = Field(
        default=3,
        ge=1,
        description="Number of priority levels for requests",
    )
    dynamic_sizing: bool = Field(
        default=True,
        description="Whether to adjust batch size dynamically",
    )


class CacheConfig(BaseModel):
    """Configuration for caching."""

    backend: str = Field(
        default="memory",
        description="Cache backend to use (memory, redis)",
    )
    ttl: Optional[int] = Field(
        default=3600,
        ge=0,
        description="Default TTL for cache entries in seconds",
    )
    max_size: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum number of items in cache",
    )
    eviction_policy: str = Field(
        default="lru",
        description="Cache eviction policy (lru, lfu, fifo)",
    )
    semantic_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for semantic cache hits",
    )


class TokenConfig(BaseModel):
    """Configuration for token management."""

    default_budget: int = Field(
        default=100000,
        ge=0,
        description="Default token budget per user",
    )
    max_budget: int = Field(
        default=1000000,
        ge=0,
        description="Maximum token budget per user",
    )
    refill_rate: Optional[int] = Field(
        default=None,
        ge=0,
        description="Tokens to refill per hour",
    )
    max_request_tokens: int = Field(
        default=4096,
        ge=0,
        description="Maximum tokens per request",
    )
    reserve_tokens: int = Field(
        default=1000,
        ge=0,
        description="Tokens to reserve for system operations",
    )


class RouteConfig(BaseModel):
    """Configuration for a single route."""

    model: str = Field(..., description="Model identifier for this route")
    max_tokens: int = Field(default=2048, ge=0, description="Maximum tokens for route")
    timeout: float = Field(default=30.0, ge=0.0, description="Timeout in seconds")
    cost_per_token: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost per token for this route",
    )
    priority: int = Field(
        default=0, description="Route priority (higher = more preferred)",
    )
    capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities supported by this route",
    )


class RoutingConfig(BaseModel):
    """Configuration for request routing."""

    routes: Dict[str, RouteConfig] = Field(
        default_factory=dict,
        description="Route configurations",
    )
    default_route: str = Field(
        default="default",
        description="Default route identifier",
    )
    fallback_routes: List[str] = Field(
        default_factory=list,
        description="Ordered list of fallback routes",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of routing retries",
    )
    cost_based_routing: bool = Field(
        default=True,
        description="Whether to consider cost in routing decisions",
    )


class OptimizationConfig(BaseModel):
    """Main configuration for optimization components."""

    batching: BatchingConfig = Field(default_factory=BatchingConfig)
    caching: CacheConfig = Field(default_factory=CacheConfig)
    token: TokenConfig = Field(default_factory=TokenConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    debug_mode: bool = Field(
        default=False,
        description="Whether to enable debug mode",
    )

    class Config:
        """Pydantic config."""

        validate_assignment = True
        extra = "forbid"
