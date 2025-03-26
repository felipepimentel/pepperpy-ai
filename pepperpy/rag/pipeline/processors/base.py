"""Base interfaces for text processors in the RAG pipeline."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.core.errors import PepperpyError


class TextProcessingError(PepperpyError):
    """Error raised during text processing."""

    pass


@dataclass
class ProcessedText:
    """Result of text processing.

    Attributes:
        text: The original text
        tokens: List of tokens
        entities: Named entities found in the text
        metadata: Additional metadata from processing
    """

    text: str
    tokens: List[str]
    entities: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingOptions:
    """Options for text processing.

    Attributes:
        model: Model to use for processing
        disable: List of processing steps to disable
        additional_options: Additional provider-specific options
    """

    model: str = "default"
    disable: List[str] = field(default_factory=list)
    additional_options: Dict[str, Any] = field(default_factory=dict)


class TextProcessor(Protocol):
    """Protocol for text processors."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the processor."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    @abstractmethod
    async def process(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process the given text.

        Args:
            text: Text to process
            options: Optional processing options

        Returns:
            Processed text result

        Raises:
            TextProcessingError: If processing fails
        """
        ...

    @abstractmethod
    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process multiple texts.

        Args:
            texts: List of texts to process
            options: Optional processing options

        Returns:
            List of processed text results

        Raises:
            TextProcessingError: If processing fails
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the processor name."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """Get the processor capabilities."""
        ...
