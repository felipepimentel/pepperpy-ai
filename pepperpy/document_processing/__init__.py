"""Document processing package.

This package provides functionality for processing different types of documents,
including text extraction, metadata extraction, OCR, and integration with RAG.
"""

from .archives import (
    ArchiveError,
    ArchiveHandler,
    get_archive_handler,
)
from .base import (
    DocumentProcessingError,
    DocumentProcessingProvider,
    create_provider,
)
from .batch import (
    BatchProcessingError,
    BatchProcessor,
    BatchResult,
    get_batch_processor,
)
from .cache import (
    DocumentCache,
    DocumentCacheError,
    get_document_cache,
)
from .filtering import (
    DocumentFilter,
    DocumentFilterError,
    FilterCondition,
    FilterOperator,
    FilterType,
    SectionExtractor,
    get_section_extractor,
)
from .integration import (
    DocumentRAGError,
    DocumentRAGProcessor,
    get_document_rag_processor,
)
from .lazy import (
    LazyProviderProxy,
    get_lazy_provider,
    is_module_available,
    register_builtin_providers,
    register_lazy_provider,
)
from .ocr import (
    OCRError,
    OCRProcessor,
    get_ocr_processor,
)
from .protected import (
    PasswordStore,
    ProtectedDocumentError,
    ProtectedDocumentHandler,
    get_protected_document_handler,
)
from .providers import (
    DoclingProvider,
    LangChainProvider,
    LlamaParseProvider,
    PyMuPDFProvider,
)
from .semantic import (
    Entity,
    Relationship,
    SemanticExtractionError,
    SemanticExtractionResult,
    SemanticExtractor,
    get_semantic_extractor,
)
from .text_normalization import (
    TextNormalizationError,
    TextNormalizer,
    get_text_normalizer,
)

__all__ = [
    # Base
    "DocumentProcessingProvider",
    "DocumentProcessingError",
    "create_provider",
    # Providers
    "PyMuPDFProvider",
    "LangChainProvider",
    "DoclingProvider",
    "LlamaParseProvider",
    # Cache
    "DocumentCache",
    "DocumentCacheError",
    "get_document_cache",
    # Lazy loading
    "LazyProviderProxy",
    "register_lazy_provider",
    "get_lazy_provider",
    "is_module_available",
    "register_builtin_providers",
    # Archive handling
    "ArchiveHandler",
    "ArchiveError",
    "get_archive_handler",
    # Batch processing
    "BatchProcessor",
    "BatchProcessingError",
    "BatchResult",
    "get_batch_processor",
    # OCR
    "OCRProcessor",
    "OCRError",
    "get_ocr_processor",
    # Text normalization
    "TextNormalizer",
    "TextNormalizationError",
    "get_text_normalizer",
    # Semantic extraction
    "SemanticExtractor",
    "SemanticExtractionError",
    "Entity",
    "Relationship",
    "SemanticExtractionResult",
    "get_semantic_extractor",
    # Document filtering
    "DocumentFilter",
    "FilterCondition",
    "FilterType",
    "FilterOperator",
    "DocumentFilterError",
    "SectionExtractor",
    "get_section_extractor",
    # Protected documents
    "PasswordStore",
    "ProtectedDocumentHandler",
    "ProtectedDocumentError",
    "get_protected_document_handler",
    # RAG integration
    "DocumentRAGProcessor",
    "DocumentRAGError",
    "get_document_rag_processor",
]
