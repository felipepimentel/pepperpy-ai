"""Chat capability configuration."""

from typing import Any, NotRequired

from ..config import CapabilityConfig


class ChatConfig(CapabilityConfig, total=False):
    """Chat capability configuration."""

    # Optional fields
    name: NotRequired[str]
    version: NotRequired[str]
    enabled: NotRequired[bool]
    metadata: NotRequired[dict[str, Any]]
    settings: NotRequired[dict[str, Any]]
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization_id: NotRequired[str]
