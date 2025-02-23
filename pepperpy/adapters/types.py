"""Adapter type system.

This module provides type definitions for the adapter system.
"""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, Optional, Set, Type, TypeVar

from pydantic import BaseModel, Field


class AdapterType(enum.Enum):
    """Adapter type enumeration."""

    FRAMEWORK = "framework"  # Framework adapters (e.g., LangChain, AutoGen)
    MODEL = "model"  # Model adapters (e.g., OpenAI, Anthropic)
    DATA = "data"  # Data adapters (e.g., JSON, CSV)
    PROTOCOL = "protocol"  # Protocol adapters (e.g., HTTP, WebSocket)
    CUSTOM = "custom"  # Custom adapters


class AdapterState(enum.Enum):
    """Adapter state enumeration."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class AdapterMetadata:
    """Adapter metadata class."""

    name: str
    type: AdapterType
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)


class AdapterConfig(BaseModel):
    """Adapter configuration model."""

    name: str = Field(..., description="Adapter name")
    type: AdapterType = Field(..., description="Adapter type")
    version: str = Field("1.0.0", description="Adapter version")
    description: Optional[str] = Field(None, description="Adapter description")
    author: Optional[str] = Field(None, description="Adapter author")
    license: Optional[str] = Field(None, description="Adapter license")
    tags: Set[str] = Field(default_factory=set, description="Adapter tags")
    dependencies: Set[str] = Field(
        default_factory=set, description="Adapter dependencies"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Adapter settings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AdapterCapabilities(BaseModel):
    """Adapter capabilities model."""

    supports_async: bool = Field(
        True, description="Whether adapter supports async operations"
    )
    supports_streaming: bool = Field(
        False, description="Whether adapter supports streaming"
    )
    supports_batching: bool = Field(
        False, description="Whether adapter supports batching"
    )
    supports_caching: bool = Field(
        False, description="Whether adapter supports caching"
    )
    supports_validation: bool = Field(
        True, description="Whether adapter supports validation"
    )
    supports_conversion: bool = Field(
        True, description="Whether adapter supports data conversion"
    )
    supported_formats: Set[str] = Field(
        default_factory=set, description="Supported data formats"
    )
    custom_capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Custom capabilities"
    )


class AdapterMetrics(BaseModel):
    """Adapter metrics model."""

    total_calls: int = Field(0, description="Total number of adapter calls")
    successful_calls: int = Field(0, description="Number of successful calls")
    failed_calls: int = Field(0, description="Number of failed calls")
    total_latency: float = Field(0.0, description="Total latency in seconds")
    average_latency: float = Field(0.0, description="Average latency in seconds")
    last_call: Optional[datetime] = Field(None, description="Last call timestamp")
    last_error: Optional[str] = Field(None, description="Last error message")
    custom_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metrics"
    )


class AdapterValidation(BaseModel):
    """Adapter validation model."""

    input_schema: Optional[Dict[str, Any]] = Field(
        None, description="Input validation schema"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        None, description="Output validation schema"
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        None, description="Config validation schema"
    )
    custom_validators: Dict[str, Any] = Field(
        default_factory=dict, description="Custom validators"
    )


class AdapterContext(BaseModel):
    """Adapter context model."""

    adapter_id: str = Field(..., description="Adapter ID")
    config: AdapterConfig = Field(..., description="Adapter configuration")
    capabilities: AdapterCapabilities = Field(
        default_factory=lambda: AdapterCapabilities(),
        description="Adapter capabilities",
    )
    metrics: AdapterMetrics = Field(
        default_factory=lambda: AdapterMetrics(),
        description="Adapter metrics",
    )
    validation: AdapterValidation = Field(
        default_factory=lambda: AdapterValidation(),
        description="Adapter validation",
    )
    state: AdapterState = Field(AdapterState.CREATED, description="Adapter state")
    custom_context: Dict[str, Any] = Field(
        default_factory=dict, description="Custom context data"
    )


# Type variables for generic adapters
T_Config = TypeVar("T_Config", bound=AdapterConfig)
T_Context = TypeVar("T_Context", bound=AdapterContext)
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")


class AdapterResult(BaseModel, Generic[T_Output]):
    """Adapter result model."""

    success: bool = Field(..., description="Whether adaptation was successful")
    output: Optional[T_Output] = Field(None, description="Adapted output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Result metrics")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Result metadata"
    )


class AdapterSpec(BaseModel):
    """Adapter specification model."""

    name: str = Field(..., description="Adapter name")
    type: AdapterType = Field(..., description="Adapter type")
    version: str = Field("1.0.0", description="Adapter version")
    description: Optional[str] = Field(None, description="Adapter description")
    config_class: Type[AdapterConfig] = Field(..., description="Configuration class")
    context_class: Type[AdapterContext] = Field(..., description="Context class")
    input_type: Any = Field(Any, description="Input type")
    output_type: Any = Field(Any, description="Output type")
    capabilities: AdapterCapabilities = Field(
        default_factory=lambda: AdapterCapabilities(),
        description="Adapter capabilities",
    )
    validation: AdapterValidation = Field(
        default_factory=lambda: AdapterValidation(),
        description="Adapter validation",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
