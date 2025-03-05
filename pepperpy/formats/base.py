"""Base classes and interfaces for the unified format handling system.

This module provides the core abstractions for the format handling system:
- FormatHandler: Base interface for all format handlers
- FormatConverter: Interface for converting between formats
- FormatValidator: Interface for validating format compliance
- FormatRegistry: Registry for managing format handlers and converters
- FormatError: Base exception for format-related errors
- BaseProcessor: Base class for data processors
- BaseTransformer: Base class for data transformers
- BaseValidator: Base class for data validators
"""

import abc
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Type variable for generic format handlers
T = TypeVar("T")
U = TypeVar("U")


class FormatError(Exception):
    """Base exception for format-related errors."""


class FormatHandler(Generic[T], abc.ABC):
    """Base interface for all format handlers."""

    @property
    @abc.abstractmethod
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """

    @property
    @abc.abstractmethod
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """

    @abc.abstractmethod
    def serialize(self, data: T) -> bytes:
        """Serialize data to bytes.

        Args:
            data: Data to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """

    @abc.abstractmethod
    def deserialize(self, data: bytes) -> T:
        """Deserialize bytes to data.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized data

        Raises:
            FormatError: If deserialization fails

        """

    def validate(self, data: bytes) -> bool:
        """Validate that the bytes conform to this format.

        Args:
            data: Bytes to validate

        Returns:
            True if valid, False otherwise

        """
        try:
            self.deserialize(data)
            return True
        except FormatError:
            return False


class FormatConverter(abc.ABC):
    """Interface for converting between formats."""

    @abc.abstractmethod
    def convert(
        self,
        data: bytes,
        source_format: FormatHandler,
        target_format: FormatHandler,
    ) -> bytes:
        """Convert data from one format to another.

        Args:
            data: Data in source format
            source_format: Source format handler
            target_format: Target format handler

        Returns:
            Data in target format

        Raises:
            FormatError: If conversion fails

        """


class FormatValidator(abc.ABC):
    """Interface for validating format compliance."""

    @abc.abstractmethod
    def validate(self, data: bytes, format_handler: FormatHandler) -> bool:
        """Validate that the bytes conform to the specified format.

        Args:
            data: Bytes to validate
            format_handler: Format handler to use for validation

        Returns:
            True if valid, False otherwise

        """


class FormatRegistry:
    """Registry for managing format handlers and converters."""

    def __init__(self):
        """Initialize the registry."""
        self._handlers: Dict[str, FormatHandler] = {}  # MIME type -> handler
        self._extensions: Dict[str, FormatHandler] = {}  # extension -> handler

    def register(self, handler: FormatHandler) -> None:
        """Register a format handler.

        Args:
            handler: Format handler to register

        """
        # Register by MIME type
        self._handlers[handler.mime_type] = handler

        # Register by file extensions
        for ext in handler.file_extensions:
            self._extensions[ext.lower()] = handler

    def get_by_mime_type(self, mime_type: str) -> Optional[FormatHandler]:
        """Get a format handler by MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            Format handler or None if not found

        """
        return self._handlers.get(mime_type)

    def get_by_extension(self, extension: str) -> Optional[FormatHandler]:
        """Get a format handler by file extension.

        Args:
            extension: File extension (without dot)

        Returns:
            Format handler or None if not found

        """
        return self._extensions.get(extension.lower())

    def get_all_handlers(self) -> List[FormatHandler]:
        """Get all registered format handlers.

        Returns:
            List of all format handlers

        """
        return list(set(self._handlers.values()))

    def get_all_mime_types(self) -> List[str]:
        """Get all registered MIME types.

        Returns:
            List of all MIME types

        """
        return list(self._handlers.keys())

    def get_all_extensions(self) -> List[str]:
        """Get all registered file extensions.

        Returns:
            List of all file extensions

        """
        return list(self._extensions.keys())


class BaseProcessor(Generic[T, U], abc.ABC):
    """Base class for data processors."""

    def __init__(self, name: str) -> None:
        """Initialize processor.

        Args:
            name: Processor name

        """
        self.name = name

    @abc.abstractmethod
    async def process(self, data: T, **kwargs: Any) -> U:
        """Process data.

        Args:
            data: Data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed data

        """


class BaseTransformer(Generic[T, U], abc.ABC):
    """Base class for data transformers."""

    def __init__(self, name: str) -> None:
        """Initialize transformer.

        Args:
            name: Transformer name

        """
        self.name = name

    @abc.abstractmethod
    async def transform(self, data: T) -> U:
        """Transform data.

        Args:
            data: Data to transform

        Returns:
            Transformed data

        """


class BaseValidator(Generic[T], abc.ABC):
    """Base class for data validators."""

    def __init__(self, name: str) -> None:
        """Initialize validator.

        Args:
            name: Validator name

        """
        self.name = name

    @abc.abstractmethod
    async def validate(self, data: T) -> bool:
        """Validate data.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise

        """


class FormatProcessor(abc.ABC):
    """Base class for format processors.

    Format processors provide a unified interface for working with different data formats.
    They handle loading, saving, and converting between formats.
    """

    def __init__(self, registry: Optional[FormatRegistry] = None) -> None:
        """Initialize format processor.

        Args:
            registry: Optional format registry to use
        """
        self.registry = registry or FormatRegistry()

    def register_handler(self, handler: FormatHandler) -> None:
        """Register a format handler.

        Args:
            handler: Format handler to register
        """
        self.registry.register(handler)

    def get_handler_by_mime_type(self, mime_type: str) -> Optional[FormatHandler]:
        """Get a format handler by MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            Format handler or None if not found
        """
        return self.registry.get_by_mime_type(mime_type)

    def get_handler_by_extension(self, extension: str) -> Optional[FormatHandler]:
        """Get a format handler by file extension.

        Args:
            extension: File extension (without dot)

        Returns:
            Format handler or None if not found
        """
        return self.registry.get_by_extension(extension)

    def get_supported_formats(self) -> List[FormatHandler]:
        """Get all supported formats.

        Returns:
            List of all format handlers
        """
        return self.registry.get_all_handlers()

    def get_supported_mime_types(self) -> List[str]:
        """Get all supported MIME types.

        Returns:
            List of all MIME types
        """
        return self.registry.get_all_mime_types()

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions.

        Returns:
            List of all file extensions
        """
        return self.registry.get_all_extensions()

    @abc.abstractmethod
    def load_file(self, file_path: str) -> Any:
        """Load data from a file.

        Args:
            file_path: Path to the file

        Returns:
            Loaded data

        Raises:
            FormatError: If the file format is not supported or loading fails
        """

    @abc.abstractmethod
    def save_file(self, data: Any, file_path: str) -> None:
        """Save data to a file.

        Args:
            data: Data to save
            file_path: Path to save the file

        Raises:
            FormatError: If the file format is not supported or saving fails
        """

    @abc.abstractmethod
    def convert_format(self, data: Any, source_format: str, target_format: str) -> Any:
        """Convert data from one format to another.

        Args:
            data: Data to convert
            source_format: Source format (MIME type or extension)
            target_format: Target format (MIME type or extension)

        Returns:
            Converted data

        Raises:
            FormatError: If the source or target format is not supported or conversion fails
        """
