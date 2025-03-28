"""Document processing workflow recipe.

This module provides workflow pipeline stages for document processing,
including text extraction, OCR, classification, and metadata extraction.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

from PIL import Image

from pepperpy.workflow.base import PipelineStage


# Define a protocol for context objects to support duck typing
class ContextProtocol(Protocol):
    """Protocol for context objects used in pipeline stages."""

    metadata: Dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context data."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set value in context data."""
        ...


class TextExtractionStage(PipelineStage):
    """Stage for extracting text from various document formats."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize text extraction stage.

        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="text_extraction", description="Extract text from documents"
        )
        self._config = kwargs

    async def _initialize(self) -> None:
        """Initialize extraction resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up extraction resources."""
        pass

    async def process(self, document_path: Union[str, Path], context: Any) -> str:
        """Extract text from document.

        Args:
            document_path: Path to document
            context: Pipeline context

        Returns:
            Extracted text

        Raises:
            ValueError: If text extraction fails
        """
        try:
            # Convert to Path object if string
            if isinstance(document_path, str):
                document_path = Path(document_path)

            # Check if file exists
            if not document_path.exists():
                raise ValueError(f"File not found: {document_path}")

            # Get file extension (lowercase)
            ext = document_path.suffix.lower()

            # Set document format in context
            context.metadata["document_format"] = (
                ext[1:] if ext.startswith(".") else ext
            )
            context.metadata["document_path"] = str(document_path)
            context.metadata["document_name"] = document_path.name

            # Extract text based on format
            if ext in [".pdf"]:
                # Try to extract PDF text with PyMuPDF if available
                try:
                    import fitz  # PyMuPDF

                    return self._extract_pdf_with_pymupdf(document_path)
                except ImportError:
                    # Fallback to basic text reading
                    return f"PDF file: {document_path.name} (PDF extraction requires PyMuPDF)"

            elif ext in [".docx", ".doc"]:
                # Try to extract DOCX text with python-docx if available
                try:
                    import docx

                    return self._extract_docx(document_path)
                except ImportError:
                    # Fallback to basic text reading
                    return f"Word document: {document_path.name} (DOCX extraction requires python-docx)"

            elif ext in [".txt", ".md", ".json", ".csv"]:
                # Text file - read directly
                with open(document_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                # Unsupported format
                return f"Unsupported document format: {ext} - {document_path.name}"

        except Exception as e:
            raise ValueError(f"Text extraction failed: {e}")

    def _extract_pdf_with_pymupdf(self, document_path: Path) -> str:
        """Extract text from PDF document using PyMuPDF."""
        import fitz  # PyMuPDF

        pdf = fitz.open(document_path)
        text = ""

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text += page.get_text()
            # Add page separator
            text += f"\n\n--- Page {page_num + 1} ---\n\n"

        return text

    def _extract_docx(self, document_path: Path) -> str:
        """Extract text from DOCX document using python-docx."""
        import docx

        doc = docx.Document(document_path)
        return "\n".join(p.text for p in doc.paragraphs)


class OCRStage(PipelineStage):
    """Stage for performing OCR on images."""

    def __init__(self, lang: str = "eng", **kwargs: Any) -> None:
        """Initialize OCR stage.

        Args:
            lang: Language for OCR
            **kwargs: Additional configuration options
        """
        super().__init__(name="ocr", description="Perform OCR on images")
        self._lang = lang
        self._config = kwargs
        self._pytesseract = None

    async def _initialize(self) -> None:
        """Initialize OCR resources."""
        try:
            # Try to import pytesseract
            import pytesseract

            self._pytesseract = pytesseract
        except ImportError:
            raise ValueError("pytesseract is required for OCR but not installed")

    async def _cleanup(self) -> None:
        """Clean up OCR resources."""
        pass

    async def process(self, image: Image.Image, context: Any) -> str:
        """Extract text from image using OCR.

        Args:
            image: Input image
            context: Pipeline context

        Returns:
            Extracted text

        Raises:
            ValueError: If OCR fails
        """
        try:
            # Initialize if needed
            if not self._pytesseract:
                await self._initialize()

            if not self._pytesseract:
                return "OCR failed: pytesseract not available"

            # Perform OCR
            text = self._pytesseract.image_to_string(image, lang=self._lang)

            # Store metadata
            context.metadata["ocr_lang"] = self._lang
            try:
                context.metadata["ocr_confidence"] = self._pytesseract.image_to_data(
                    image, lang=self._lang, output_type=self._pytesseract.Output.DICT
                )["conf"]
            except:
                # Skip if confidence extraction fails
                pass

            return text

        except Exception as e:
            raise ValueError(f"OCR failed: {e}")


class DocumentClassificationStage(PipelineStage):
    """Stage for classifying documents by type and content."""

    def __init__(
        self,
        model: str = "default",
        **kwargs: Any,
    ) -> None:
        """Initialize classification stage.

        Args:
            model: Classification model to use
            **kwargs: Additional configuration options
        """
        super().__init__(name="classification", description="Classify document content")
        self._model = model
        self._config = kwargs

    async def _initialize(self) -> None:
        """Initialize classification resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up classification resources."""
        pass

    async def process(self, text: str, context: Any) -> Dict[str, Any]:
        """Classify document content.

        Args:
            text: Document text
            context: Pipeline context

        Returns:
            Classification results

        Raises:
            ValueError: If classification fails
        """
        try:
            # Perform basic classification
            results = {
                "document_type": self._classify_type(text),
                "content_category": self._classify_category(text),
                "language": self._detect_language(text),
                "confidence": 0.85,  # Placeholder
            }

            # Store metadata
            context.metadata["classification_model"] = self._model
            context.metadata["classification_results"] = results

            return results

        except Exception as e:
            raise ValueError(f"Classification failed: {e}")

    def _classify_type(self, text: str) -> str:
        """Classify document type based on content patterns."""
        # Simplified classification logic
        text_lower = text.lower()

        if "invoice" in text_lower or "receipt" in text_lower:
            return "invoice"
        elif "report" in text_lower:
            return "report"
        elif "agreement" in text_lower or "contract" in text_lower:
            return "legal"
        elif "resume" in text_lower or "cv" in text_lower:
            return "resume"
        else:
            return "other"

    def _classify_category(self, text: str) -> str:
        """Classify document category based on content."""
        # Simplified classification logic
        text_lower = text.lower()

        if "financial" in text_lower or "budget" in text_lower or "cost" in text_lower:
            return "financial"
        elif "technical" in text_lower or "specification" in text_lower:
            return "technical"
        elif (
            "legal" in text_lower
            or "agreement" in text_lower
            or "contract" in text_lower
        ):
            return "legal"
        else:
            return "general"

    def _detect_language(self, text: str) -> str:
        """Detect document language."""
        # Simplified language detection
        # Real implementation would use a language detection library
        return "en"  # Default to English


class MetadataExtractionStage(PipelineStage):
    """Stage for extracting metadata from documents."""

    def __init__(
        self,
        extractors: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize metadata extraction stage.

        Args:
            extractors: List of metadata extractors to use
            **kwargs: Additional configuration options
        """
        super().__init__(name="metadata", description="Extract metadata from documents")
        self._extractors = extractors or ["dates", "entities", "keywords"]
        self._config = kwargs

    async def _initialize(self) -> None:
        """Initialize extraction resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up extraction resources."""
        pass

    async def process(self, text: str, context: Any) -> Dict[str, Any]:
        """Extract metadata from document.

        Args:
            text: Document text
            context: Pipeline context

        Returns:
            Extracted metadata

        Raises:
            ValueError: If metadata extraction fails
        """
        try:
            metadata = {}

            # Apply each extractor
            for extractor in self._extractors:
                if extractor == "dates":
                    metadata["dates"] = self._extract_dates(text)
                elif extractor == "entities":
                    metadata["entities"] = self._extract_entities(text)
                elif extractor == "keywords":
                    metadata["keywords"] = self._extract_keywords(text)

            # Store metadata
            context.metadata["metadata_extractors"] = self._extractors
            context.metadata["extraction_results"] = metadata

            return metadata

        except Exception as e:
            raise ValueError(f"Metadata extraction failed: {e}")

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Simple regex-based date extraction
        date_pattern = r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
        return re.findall(date_pattern, text)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        # Simplified entity extraction - real implementation would use NLP
        entities = {
            "organizations": [],
            "persons": [],
            "locations": [],
        }

        # Very simple rule-based extraction as fallback
        words = text.split()
        for word in words:
            if word.startswith("@"):
                entities["persons"].append(word[1:])
            elif word.startswith("#"):
                entities["organizations"].append(word[1:])

        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple word frequency analysis
        words = text.lower().split()
        # Filter out common stop words and short words
        stop_words = {
            "the",
            "and",
            "a",
            "an",
            "in",
            "of",
            "to",
            "is",
            "for",
            "on",
            "with",
        }
        filtered_words = [w for w in words if len(w) > 4 and w not in stop_words]

        # Count word frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top 10 keywords
        return [word for word, _ in sorted_words[:10]]
