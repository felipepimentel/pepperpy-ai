"""Text processing exceptions."""

from ..exceptions import PepperPyAIError


class TextError(PepperPyAIError):
    """Raised when there is an error with text processing."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
        """
        super().__init__(message)


class TextProcessingError(TextError):
    """Base exception for text processing errors."""

    pass


class ChunkingError(TextProcessingError):
    """Error during text chunking."""

    pass


class ProcessingError(TextProcessingError):
    """Error during text processing."""

    pass


class ValidationError(TextProcessingError):
    """Error during text validation."""

    pass
