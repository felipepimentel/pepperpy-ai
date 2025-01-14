"""Text processor module."""

from abc import ABC, abstractmethod
from typing import TypedDict


class ProcessorParams(TypedDict, total=False):
    """Text processor parameters."""

    lowercase: bool | None
    remove_punctuation: bool | None
    remove_numbers: bool | None
    remove_whitespace: bool | None
    normalize: bool | None


class BaseTextProcessor(ABC):
    """Base text processor implementation."""

    @abstractmethod
    async def process(self, text: str, **kwargs: ProcessorParams) -> str:
        """Process text.

        Args:
            text: Text to process.
            **kwargs: Processing parameters.

        Returns:
            str: Processed text.
        """
        pass
