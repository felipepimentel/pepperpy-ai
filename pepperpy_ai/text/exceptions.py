"""Text processing exceptions."""

from ..exceptions import PepperpyError


class TextProcessingError(PepperpyError):
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
