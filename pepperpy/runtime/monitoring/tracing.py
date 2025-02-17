"""@file: tracing.py
@purpose: Runtime distributed tracing functionality
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON

logger = get_logger(__name__)


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""

    enabled: bool = True
    sample_rate: float = 1.0
    max_spans: int = 1000

    def validate(self) -> None:
        """Validate tracing configuration."""
        if not 0 <= self.sample_rate <= 1:
            raise ConfigurationError("Sample rate must be between 0 and 1")
        if self.max_spans < 1:
            raise ConfigurationError("Max spans must be positive")


@dataclass
class Tracer:
    """Distributed tracing for runtime operations."""

    name: str
    id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def end(self) -> None:
        """End the trace span."""
        self.end_time = datetime.utcnow()

    def to_json(self) -> JSON:
        """Convert tracer to JSON format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "attributes": self.attributes,
        }
