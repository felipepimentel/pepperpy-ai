"""Document transformation pipeline for RAG.

This module provides a pipeline for transforming documents in the RAG system,
including text normalization, cleaning, and other transformations that improve
retrieval quality.
"""

import re
import string
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.types.common import Document, Metadata

# Set up telemetry
telemetry = get_provider_telemetry("rag_transform")


class TransformationType(Enum):
    """Types of document transformations."""

    NORMALIZE = "normalize"  # Unicode normalization
    CLEAN = "clean"  # Remove unwanted characters
    LOWERCASE = "lowercase"  # Convert to lowercase
    REMOVE_STOPWORDS = "remove_stopwords"  # Remove common stopwords
    REMOVE_PUNCTUATION = "remove_punctuation"  # Remove punctuation
    REMOVE_WHITESPACE = "remove_whitespace"  # Remove excess whitespace
    REMOVE_HTML = "remove_html"  # Remove HTML tags
    REMOVE_URLS = "remove_urls"  # Remove URLs
    REMOVE_NUMBERS = "remove_numbers"  # Remove numeric values
    STEM = "stem"  # Apply stemming
    LEMMATIZE = "lemmatize"  # Apply lemmatization
    CUSTOM = "custom"  # Custom transformation


@dataclass
class TransformationConfig:
    """Configuration for document transformations.

    This class defines the configuration for document transformations, including
    which transformations to apply and their parameters.
    """

    enabled: bool = True  # Whether transformations are enabled
    include_types: Optional[List[TransformationType]] = None  # Types to include
    exclude_types: Optional[List[TransformationType]] = None  # Types to exclude
    preserve_original: bool = True  # Whether to preserve the original content
    custom_transformers: Dict[str, Callable[[str], str]] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)  # Additional parameters


class DocumentTransformer(ABC):
    """Base class for document transformers.

    This abstract class defines the interface for document transformers, which
    apply specific transformations to documents.
    """

    def __init__(self, config: Optional[TransformationConfig] = None):
        """Initialize the document transformer.

        Args:
            config: Optional configuration for the transformer.
        """
        self.config = config or TransformationConfig()

    @abstractmethod
    def transform(self, text: str) -> str:
        """Transform document text.

        Args:
            text: The text to transform.

        Returns:
            The transformed text.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this transformer is enabled.

        Returns:
            True if the transformer is enabled, False otherwise.
        """
        return self.config.enabled

    def should_transform_type(self, transform_type: TransformationType) -> bool:
        """Check if this transformer should apply the specified type.

        Args:
            transform_type: The type of transformation to check.

        Returns:
            True if the type should be applied, False otherwise.
        """
        if not self.config.enabled:
            return False

        if self.config.include_types is not None:
            return transform_type in self.config.include_types

        if self.config.exclude_types is not None:
            return transform_type not in self.config.exclude_types

        return True


class TextNormalizer(DocumentTransformer):
    """Transformer for normalizing text.

    This transformer applies Unicode normalization to text, converting it to
    a canonical form.
    """

    def transform(self, text: str) -> str:
        """Normalize text.

        Args:
            text: The text to normalize.

        Returns:
            The normalized text.
        """
        if not self.should_transform_type(TransformationType.NORMALIZE):
            return text

        telemetry.info(
            "text_normalization_started",
            "Normalizing text",
        )

        # Apply Unicode normalization (NFC form by default)
        form = self.config.params.get("normalization_form", "NFC")
        normalized_text = unicodedata.normalize(form, text)

        telemetry.info(
            "text_normalization_completed",
            "Text normalized",
        )

        return normalized_text


class TextCleaner(DocumentTransformer):
    """Transformer for cleaning text.

    This transformer removes unwanted characters and patterns from text.
    """

    def transform(self, text: str) -> str:
        """Clean text.

        Args:
            text: The text to clean.

        Returns:
            The cleaned text.
        """
        if not self.should_transform_type(TransformationType.CLEAN):
            return text

        telemetry.info(
            "text_cleaning_started",
            "Cleaning text",
        )

        cleaned_text = text

        # Remove HTML tags if enabled
        if self.should_transform_type(TransformationType.REMOVE_HTML):
            cleaned_text = re.sub(r"<[^>]+>", " ", cleaned_text)

        # Remove URLs if enabled
        if self.should_transform_type(TransformationType.REMOVE_URLS):
            cleaned_text = re.sub(r"https?://\S+|www\.\S+", " ", cleaned_text)

        # Remove numbers if enabled
        if self.should_transform_type(TransformationType.REMOVE_NUMBERS):
            cleaned_text = re.sub(r"\d+", " ", cleaned_text)

        # Remove punctuation if enabled
        if self.should_transform_type(TransformationType.REMOVE_PUNCTUATION):
            translator = str.maketrans("", "", string.punctuation)
            cleaned_text = cleaned_text.translate(translator)

        # Remove excess whitespace
        if self.should_transform_type(TransformationType.REMOVE_WHITESPACE):
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        telemetry.info(
            "text_cleaning_completed",
            "Text cleaned",
        )

        return cleaned_text


class TextCaseTransformer(DocumentTransformer):
    """Transformer for changing text case.

    This transformer converts text to lowercase or uppercase.
    """

    def transform(self, text: str) -> str:
        """Transform text case.

        Args:
            text: The text to transform.

        Returns:
            The transformed text.
        """
        if not self.should_transform_type(TransformationType.LOWERCASE):
            return text

        telemetry.info(
            "text_case_transformation_started",
            "Transforming text case",
        )

        # Convert to lowercase
        transformed_text = text.lower()

        telemetry.info(
            "text_case_transformation_completed",
            "Text case transformed",
        )

        return transformed_text


class StopwordRemover(DocumentTransformer):
    """Transformer for removing stopwords.

    This transformer removes common stopwords from text.
    """

    def transform(self, text: str) -> str:
        """Remove stopwords from text.

        Args:
            text: The text to transform.

        Returns:
            The text with stopwords removed.
        """
        if not self.should_transform_type(TransformationType.REMOVE_STOPWORDS):
            return text

        telemetry.info(
            "stopword_removal_started",
            "Removing stopwords",
        )

        # Define common English stopwords
        # In a real implementation, this would be more comprehensive and language-aware
        stopwords = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "because",
            "as",
            "what",
            "which",
            "this",
            "that",
            "these",
            "those",
            "then",
            "just",
            "so",
            "than",
            "such",
            "when",
            "who",
            "how",
            "where",
            "why",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "having",
            "do",
            "does",
            "did",
            "doing",
            "to",
            "from",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "can",
            "will",
            "should",
            "now",
        }

        # Custom stopwords from configuration
        custom_stopwords = set(self.config.params.get("custom_stopwords", []))
        all_stopwords = stopwords.union(custom_stopwords)

        # Remove stopwords
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in all_stopwords]
        filtered_text = " ".join(filtered_words)

        telemetry.info(
            "stopword_removal_completed",
            "Stopwords removed",
        )

        return filtered_text


class TextStemmer(DocumentTransformer):
    """Transformer for stemming text.

    This transformer applies stemming to text, reducing words to their root form.
    """

    def transform(self, text: str) -> str:
        """Apply stemming to text.

        Args:
            text: The text to transform.

        Returns:
            The stemmed text.
        """
        if not self.should_transform_type(TransformationType.STEM):
            return text

        telemetry.info(
            "text_stemming_started",
            "Stemming text",
        )

        # Simple stemming implementation
        # In a real implementation, this would use a proper stemming algorithm
        # like Porter or Snowball stemmer
        words = text.split()
        stemmed_words = []

        for word in words:
            # Very basic stemming rules (for demonstration only)
            if word.endswith("ing"):
                stemmed_word = word[:-3]
            elif word.endswith("ed"):
                stemmed_word = word[:-2]
            elif word.endswith("s") and not word.endswith("ss"):
                stemmed_word = word[:-1]
            elif word.endswith("ly"):
                stemmed_word = word[:-2]
            else:
                stemmed_word = word
            stemmed_words.append(stemmed_word)

        stemmed_text = " ".join(stemmed_words)

        telemetry.info(
            "text_stemming_completed",
            "Text stemmed",
        )

        return stemmed_text


class TextLemmatizer(DocumentTransformer):
    """Transformer for lemmatizing text.

    This transformer applies lemmatization to text, reducing words to their
    dictionary form.
    """

    def transform(self, text: str) -> str:
        """Apply lemmatization to text.

        Args:
            text: The text to transform.

        Returns:
            The lemmatized text.
        """
        if not self.should_transform_type(TransformationType.LEMMATIZE):
            return text

        telemetry.info(
            "text_lemmatization_started",
            "Lemmatizing text",
        )

        # Simple lemmatization implementation
        # In a real implementation, this would use a proper lemmatization algorithm
        # with a dictionary of word forms
        words = text.split()
        lemmatized_words = []

        # Very basic lemmatization rules (for demonstration only)
        lemma_dict = {
            "am": "be",
            "is": "be",
            "are": "be",
            "was": "be",
            "were": "be",
            "has": "have",
            "had": "have",
            "having": "have",
            "does": "do",
            "did": "do",
            "doing": "do",
            "better": "good",
            "best": "good",
            "worse": "bad",
            "worst": "bad",
            "children": "child",
            "men": "man",
            "women": "woman",
            "mice": "mouse",
            "geese": "goose",
            "feet": "foot",
            "teeth": "tooth",
        }

        for word in words:
            lower_word = word.lower()
            if lower_word in lemma_dict:
                lemmatized_word = lemma_dict[lower_word]
                # Preserve case if possible
                if word.isupper():
                    lemmatized_word = lemmatized_word.upper()
                elif word[0].isupper():
                    lemmatized_word = lemmatized_word.capitalize()
            else:
                lemmatized_word = word
            lemmatized_words.append(lemmatized_word)

        lemmatized_text = " ".join(lemmatized_words)

        telemetry.info(
            "text_lemmatization_completed",
            "Text lemmatized",
        )

        return lemmatized_text


class CustomTransformer(DocumentTransformer):
    """Transformer for custom transformations.

    This transformer applies custom transformation functions to text.
    """

    def transform(self, text: str) -> str:
        """Apply custom transformations to text.

        Args:
            text: The text to transform.

        Returns:
            The transformed text.
        """
        if not self.should_transform_type(TransformationType.CUSTOM):
            return text

        telemetry.info(
            "custom_transformation_started",
            "Applying custom transformations",
        )

        transformed_text = text

        # Apply each custom transformer
        for name, transformer_func in self.config.custom_transformers.items():
            try:
                transformed_text = transformer_func(transformed_text)
            except Exception as e:
                telemetry.error(
                    "custom_transformation_error",
                    f"Error in custom transformer '{name}'",
                    {"error": str(e)},
                )

        telemetry.info(
            "custom_transformation_completed",
            "Custom transformations applied",
        )

        return transformed_text


class DocumentTransformationPipeline:
    """Pipeline for transforming documents.

    This class provides a pipeline for transforming documents using multiple
    transformers in sequence.
    """

    def __init__(self, transformers: Optional[List[DocumentTransformer]] = None):
        """Initialize the document transformation pipeline.

        Args:
            transformers: Optional list of document transformers to use.
                If not provided, default transformers will be used.
        """
        self.transformers = transformers or self._create_default_transformers()

    def _create_default_transformers(self) -> List[DocumentTransformer]:
        """Create the default set of document transformers.

        Returns:
            A list of default document transformers.
        """
        return [
            TextNormalizer(),
            TextCleaner(),
            TextCaseTransformer(),
            StopwordRemover(),
            TextStemmer(),
            TextLemmatizer(),
        ]

    def process(self, document: Document) -> Document:
        """Process a document through the transformation pipeline.

        Args:
            document: The document to process.

        Returns:
            The transformed document.
        """
        telemetry.info(
            "document_transformation_started",
            "Transforming document",
            {"document_id": document.id},
        )

        # Get the original content
        original_content = document.content
        transformed_content = original_content

        # Apply each transformer in sequence
        for transformer in self.transformers:
            if transformer.is_enabled():
                try:
                    transformed_content = transformer.transform(transformed_content)
                except Exception as e:
                    telemetry.error(
                        "document_transformation_error",
                        f"Error in transformer {type(transformer).__name__}",
                        {"document_id": document.id, "error": str(e)},
                    )

        # Create metadata for the transformed document
        transformed_metadata = {}

        # Copy existing metadata
        if document.metadata:
            for key, value in document.metadata.to_dict().items():
                transformed_metadata[key] = value

        # Add transformation metadata
        transformed_metadata["transformed"] = True

        # Preserve original content if configured
        preserve_original = all(
            getattr(transformer, "config", TransformationConfig()).preserve_original
            for transformer in self.transformers
            if transformer.is_enabled()
        )

        if preserve_original:
            transformed_metadata["original_content"] = original_content

        # Create the transformed document
        transformed_document = Document(
            id=document.id,
            content=transformed_content,
            metadata=Metadata.from_dict(transformed_metadata),
        )

        telemetry.info(
            "document_transformation_completed",
            "Document transformed",
            {"document_id": document.id},
        )

        return transformed_document

    def batch_process(self, documents: List[Document]) -> List[Document]:
        """Process multiple documents through the transformation pipeline.

        Args:
            documents: The documents to process.

        Returns:
            The transformed documents.
        """
        telemetry.info(
            "batch_document_transformation_started",
            f"Transforming {len(documents)} documents",
            {"document_count": len(documents)},
        )

        transformed_documents = [self.process(doc) for doc in documents]

        telemetry.info(
            "batch_document_transformation_completed",
            f"Transformed {len(documents)} documents",
            {"document_count": len(documents)},
        )

        return transformed_documents


# Convenience functions


def create_transformation_pipeline(
    include_types: Optional[List[TransformationType]] = None,
    exclude_types: Optional[List[TransformationType]] = None,
    custom_transformers: Optional[Dict[str, Callable[[str], str]]] = None,
    preserve_original: bool = True,
) -> DocumentTransformationPipeline:
    """Create a document transformation pipeline with the specified configuration.

    Args:
        include_types: Optional list of transformation types to include.
        exclude_types: Optional list of transformation types to exclude.
        custom_transformers: Optional dictionary of custom transformers.
        preserve_original: Whether to preserve the original content.

    Returns:
        A configured document transformation pipeline.
    """
    # Create a configuration for the transformers
    config = TransformationConfig(
        include_types=include_types,
        exclude_types=exclude_types,
        custom_transformers=custom_transformers or {},
        preserve_original=preserve_original,
    )

    # Create transformers with the configuration
    transformers = [
        TextNormalizer(config),
        TextCleaner(config),
        TextCaseTransformer(config),
        StopwordRemover(config),
        TextStemmer(config),
        TextLemmatizer(config),
    ]

    # Add custom transformer if custom transformers are provided
    if custom_transformers:
        transformers.append(CustomTransformer(config))

    # Create and return the pipeline
    return DocumentTransformationPipeline(transformers)


def transform_document(
    document: Document,
    include_types: Optional[List[TransformationType]] = None,
    exclude_types: Optional[List[TransformationType]] = None,
    preserve_original: bool = True,
) -> Document:
    """Transform a document using the default pipeline.

    Args:
        document: The document to transform.
        include_types: Optional list of transformation types to include.
        exclude_types: Optional list of transformation types to exclude.
        preserve_original: Whether to preserve the original content.

    Returns:
        The transformed document.
    """
    pipeline = create_transformation_pipeline(
        include_types, exclude_types, preserve_original=preserve_original
    )
    return pipeline.process(document)


def transform_documents(
    documents: List[Document],
    include_types: Optional[List[TransformationType]] = None,
    exclude_types: Optional[List[TransformationType]] = None,
    preserve_original: bool = True,
) -> List[Document]:
    """Transform multiple documents using the default pipeline.

    Args:
        documents: The documents to transform.
        include_types: Optional list of transformation types to include.
        exclude_types: Optional list of transformation types to exclude.
        preserve_original: Whether to preserve the original content.

    Returns:
        The transformed documents.
    """
    pipeline = create_transformation_pipeline(
        include_types, exclude_types, preserve_original=preserve_original
    )
    return pipeline.batch_process(documents)
