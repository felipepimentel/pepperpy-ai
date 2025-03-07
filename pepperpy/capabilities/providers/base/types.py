"""Provider capability types.

This module defines the types used by provider capabilities.
"""

from typing import Any, Dict, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Type variables
T = TypeVar("T")
ProviderType = TypeVar("ProviderType", bound="ProviderCapability")


class ProviderConfig(BaseModel):
    """Provider configuration model.

    Attributes:
        id: Unique provider identifier
        type: Provider type identifier
        config: Provider-specific configuration

    """

    id: UUID = Field(default_factory=uuid4)
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
