"""Language detection and translation processor module.

This module provides functionality for detecting document language and translation.
"""

from typing import Any, Dict, List, Optional, Union

import langdetect
from langdetect.lang_detect_exception import LangDetectException
from transformers import AutoModelForSeq2SeqGeneration, AutoTokenizer

from pepperpy.errors import DocumentProcessError
from pepperpy.rag.document.processors.base import BaseDocumentProcessor
from pepperpy.rag.document.types import Document, DocumentChunk


class LanguageProcessor(BaseDocumentProcessor):
    """Language detection and translation processor.

    This processor can:
    - Detect the language of document content
    - Translate content to a target language (if specified)
    - Add language metadata to documents
    - Filter documents by language
    """

    def __init__(
        self,
        target_language: Optional[str] = None,
        min_confidence: float = 0.8,
        allowed_languages: Optional[List[str]] = None,
        translation_model: str = "Helsinki-NLP/opus-mt-mul-en",
        **kwargs: Any,
    ) -> None:
        """Initialize the language processor.

        Args:
            target_language: ISO 639-1 code of language to translate to (e.g. 'en').
            min_confidence: Minimum confidence score for language detection.
            allowed_languages: List of allowed ISO 639-1 language codes.
            translation_model: HuggingFace model ID for translation.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.target_language = target_language
        self.min_confidence = min_confidence
        self.allowed_languages = set(allowed_languages) if allowed_languages else None

        # Initialize translation model if needed
        self.translator = None
        self.tokenizer = None
        if target_language:
            self.translator = AutoModelForSeq2SeqGeneration.from_pretrained(
                translation_model
            )
            self.tokenizer = AutoTokenizer.from_pretrained(translation_model)

    def _detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of the given text.

        Args:
            text: The text to detect language for.

        Returns:
            A dictionary containing the detected language code and confidence.

        Raises:
            DocumentProcessError: If language detection fails.
        """
        try:
            # Use langdetect with more detailed output
            detection = langdetect.detect_langs(text)[0]
            return {"language": detection.lang, "confidence": detection.prob}
        except LangDetectException as e:
            raise DocumentProcessError(f"Failed to detect language: {str(e)}") from e

    def _translate_text(self, text: str, source_lang: str) -> str:
        """Translate text to the target language.

        Args:
            text: The text to translate.
            source_lang: The source language code.

        Returns:
            The translated text.

        Raises:
            DocumentProcessError: If translation fails.
        """
        if not self.translator or not self.tokenizer:
            raise DocumentProcessError("Translation model not initialized")

        try:
            # Skip translation if already in target language
            if source_lang == self.target_language:
                return text

            # Tokenize and translate
            inputs = self.tokenizer(
                text, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            outputs = self.translator.generate(**inputs)
            translated = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[
                0
            ]

            return translated

        except Exception as e:
            raise DocumentProcessError(f"Translation failed: {str(e)}") from e

    async def process(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> Union[Document, List[Document]]:
        """Process one or more documents for language detection and translation.

        Args:
            documents: A single document or list of documents to process.
            **kwargs: Additional keyword arguments for processing.

        Returns:
            The processed document(s) with language metadata and translations.

        Raises:
            DocumentProcessError: If processing fails.
        """
        try:
            if isinstance(documents, Document):
                documents = [documents]

            processed_docs = []
            for doc in documents:
                # Process each chunk
                processed_chunks = []
                for chunk in doc.chunks:
                    # Detect language
                    lang_info = self._detect_language(chunk.content)

                    # Skip if confidence is too low
                    if lang_info["confidence"] < self.min_confidence:
                        continue

                    # Skip if language not allowed
                    if (
                        self.allowed_languages
                        and lang_info["language"] not in self.allowed_languages
                    ):
                        continue

                    # Update chunk metadata with language info
                    chunk_metadata = {**(chunk.metadata or {}), "language": lang_info}

                    # Translate if needed
                    content = chunk.content
                    if self.target_language:
                        content = self._translate_text(content, lang_info["language"])
                        chunk_metadata["translated_to"] = self.target_language

                    # Create processed chunk
                    processed_chunk = DocumentChunk(
                        content=content, metadata=chunk_metadata
                    )
                    processed_chunks.append(processed_chunk)

                # Skip empty documents
                if not processed_chunks:
                    continue

                # Create processed document
                processed_doc = Document(
                    chunks=processed_chunks,
                    metadata={**(doc.metadata or {}), "language_processed": True},
                )
                processed_docs.append(processed_doc)

            return processed_docs[0] if len(processed_docs) == 1 else processed_docs

        except Exception as e:
            raise DocumentProcessError(f"Language processing failed: {str(e)}") from e
