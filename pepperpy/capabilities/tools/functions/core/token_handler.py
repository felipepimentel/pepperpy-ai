"""Token handling module."""

from typing import Any, ClassVar, Dict, Optional

from tiktoken import Encoding, encoding_for_model, get_encoding # type: ignore

from ....tools.base import BaseTool, ToolConfig

class TokenHandler(BaseTool):
    """Token handling class."""

    TOKEN_LIMITS: ClassVar[dict[str, int]] = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 4096,
    }

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize token handler.
        
        Args:
            name: Tool name
            config: Optional configuration
        """
        super().__init__(
            config=ToolConfig(
                name=name,
                description="Tool for handling tokens",
                parameters=config or {},
            )
        )
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
            
    async def _setup(self) -> None:
        """Set up tool resources."""
        pass
        
    async def _teardown(self) -> None:
        """Clean up tool resources."""
        self._encoders.clear()
        
    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute token handling operation.
        
        Args:
            input_data: Input data containing text and model
            context: Optional execution context
            
        Returns:
            Token count and encoding information
            
        Raises:
            ValueError: If input data is invalid
        """
        text = input_data.get("text")
        model = input_data.get("model", "cl100k_base")
        
        if not text:
            raise ValueError("Text is required")
            
        encoder = self._get_encoder(model)
        tokens = encoder.encode(text)
        
        return {
            "token_count": len(tokens),
            "model": model,
            "token_limit": self.TOKEN_LIMITS.get(model, 0),
        }
