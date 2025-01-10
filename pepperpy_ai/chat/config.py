"""Chat configuration."""

from dataclasses import dataclass, field

from ..config.base import BaseConfig, JsonDict
from .types import ChatRole


@dataclass
class ChatConfig(BaseConfig):
    """Chat configuration."""

    system_role: ChatRole = ChatRole.SYSTEM
    user_role: ChatRole = ChatRole.USER
    assistant_role: ChatRole = ChatRole.ASSISTANT
    system_message: str | None = None
    settings: JsonDict = field(default_factory=dict)
