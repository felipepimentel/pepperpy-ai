"""Token handling module."""

from typing import Any, ClassVar

from tiktoken import Encoding, encoding_for_model, get_encoding


class TokenHandler:
    """Token handling class."""

    TOKEN_LIMITS: ClassVar[dict[str, int]] = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 4096,
    }

    def __init__(self) -> None:
        """Initialize token handler."""
        self._encoders: dict[str, Encoding] = {}

    def _get_encoding(self, model: str) -> Encoding:
        """Get encoding for model.

        Args:
            model: Model name

        Returns:
            Encoding for model
        """
        try:
            return encoding_for_model(model)
        except:  # noqa: E722
            return get_encoding("cl100k_base")

    def _get_encoder(self, model: str) -> Any:
        """Get encoder for model."""
        try:
            return self._get_encoding(model)
        except:  # noqa: E722
            return get_encoding("cl100k_base")
