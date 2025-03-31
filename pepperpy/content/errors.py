"""Content processing errors."""

from pepperpy.core.base import PepperpyError


class ContentProcessingError(PepperpyError):
    """Base error for content processing."""

    pass


class ContentProcessingConfigError(ContentProcessingError):
    """Error raised when there is a configuration issue."""

    pass


class ContentProcessingIOError(ContentProcessingError):
    """Error raised when there is an I/O issue."""

    pass


class UnsupportedContentTypeError(ContentProcessingError):
    """Error raised when content type is not supported."""

    pass


class ProviderNotFoundError(ContentProcessingError):
    """Error raised when provider is not found."""

    pass 