"""Message and Response type definitions for the Pepperpy framework."""

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class Message(BaseModel):
    """A message that can be exchanged between components."""

    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class Response(BaseModel):
    """A response from a provider."""

    id: UUID
    content: str
    metadata: Optional[Dict[str, Any]] = None
