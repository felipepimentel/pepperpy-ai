"""Text processing configuration module."""

from .base import BaseConfig


class TextConfig(BaseConfig):
    """Configuration for text processing.

    This class provides configuration options for text processing, including
    chunking parameters, analysis settings, and other options that control
    text processing behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        enabled: bool = True,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        normalize: bool = True,
        lowercase: bool = True,
        remove_punctuation: bool = False,
        remove_numbers: bool = False,
        remove_whitespace: bool = True,
    ) -> None:
        """Initialize text processing configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            enabled: Whether text processing is enabled.
            chunk_size: Default size for text chunks.
            chunk_overlap: Overlap between chunks.
            min_chunk_size: Minimum chunk size.
            max_chunk_size: Maximum chunk size.
            normalize: Whether to normalize text.
            lowercase: Whether to convert text to lowercase.
            remove_punctuation: Whether to remove punctuation.
            remove_numbers: Whether to remove numbers.
            remove_whitespace: Whether to remove extra whitespace.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.normalize = normalize
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.remove_numbers = remove_numbers
        self.remove_whitespace = remove_whitespace
