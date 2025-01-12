"""Chat configuration module."""

from .base import BaseConfig


class ChatConfig(BaseConfig):
    """Configuration for chat capabilities.

    This class provides configuration options for chat capabilities, including
    model settings, conversation parameters, and other options that control
    chat behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        model: str,
        enabled: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        timeout: float = 30.0,
    ) -> None:
        """Initialize chat configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            model: Model name or path.
            enabled: Whether chat is enabled.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            top_p: Nucleus sampling parameter.
            frequency_penalty: Frequency penalty.
            presence_penalty: Presence penalty.
            timeout: Request timeout in seconds.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.timeout = timeout
