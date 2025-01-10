"""Network client implementation."""

from dataclasses import dataclass, field

from pepperpy_core.base import BaseData
from pepperpy_core.types import JsonDict


@dataclass
class ClientConfig(BaseData):
    """Client configuration."""

    # Required fields first
    base_url: str = ""
    name: str = ""  # From BaseData, must have default

    # Optional fields
    timeout: float = 30.0
    verify_ssl: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)
