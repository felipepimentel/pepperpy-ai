"""Text normalization for document processing.

This module provides functionality for normalizing and transforming text
extracted from documents to improve quality and consistency.
"""

import logging
import re
import string
import unicodedata
from typing import Any, Callable, Dict, List, Optional

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    import nltk

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class TextNormalizationError(PepperpyError):
    """Error raised during text normalization operations."""

    pass


class TextNormalizer:
    """Text normalizer for document processing.

    This class provides functionality for normalizing and transforming text
    extracted from documents to improve quality and consistency.
    """

    # Default transformations to apply
    DEFAULT_TRANSFORMATIONS = [
        "strip_whitespace",
        "normalize_unicode",
        "normalize_whitespace",
        "remove_control_chars",
    ]

    # Default cleanup patterns
    DEFAULT_PATTERNS = {
        "url": r"https?://\S+|www\.\S+",
        "email": r"\S+@\S+\.\S+",
        "phone": r"\+?[\d\-\(\)\s]{7,}",
        "ssn": r"\d{3}-\d{2}-\d{4}",
        "credit_card": r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}",
        "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "markdown_links": r"\[(.*?)\]\((.*?)\)",
        "html_tags": r"<[^>]*>",
        "extra_whitespace": r"\s+",
    }

    # Default replacements
    DEFAULT_REPLACEMENTS = {
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u2013": "-",  # En dash
        "\u2014": "--",  # Em dash
        "\u00a0": " ",  # Non-breaking space
        "\u00ad": "",  # Soft hyphen
        "\u00b7": "*",  # Middle dot
        "\u2022": "*",  # Bullet
        "\u2023": "*",  # Triangular bullet
        "\u2026": "...",  # Horizontal ellipsis
        "\u00ae": "(R)",  # Registered sign
        "\u00a9": "(C)",  # Copyright sign
        "\u2122": "TM",  # Trade mark sign
    }

    def __init__(
        self,
        transformations: Optional[List[str]] = None,
        custom_patterns: Optional[Dict[str, str]] = None,
        custom_replacements: Optional[Dict[str, str]] = None,
        language: str = "en",
        **kwargs: Any,
    ) -> None:
        """Initialize text normalizer.

        Args:
            transformations: List of transformation names to apply
            custom_patterns: Custom regex patterns for text cleaning
            custom_replacements: Custom character replacements
            language: Language code for language-specific processing
            **kwargs: Additional configuration options
        """
        # Set transformations
        self.transformations = transformations or self.DEFAULT_TRANSFORMATIONS

        # Set patterns
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)

        # Compile patterns
        self.compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self.patterns.items()
        }

        # Set replacements
        self.replacements = self.DEFAULT_REPLACEMENTS.copy()
        if custom_replacements:
            self.replacements.update(custom_replacements)

        # Set language
        self.language = language

        # Initialize NLP resources
        if "lemmatize" in self.transformations and NLTK_AVAILABLE:
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                logger.warning("NLTK punkt tokenizer not found. Downloading...")
                nltk.download("punkt")

            try:
                nltk.data.find("corpora/wordnet")
            except LookupError:
                logger.warning("NLTK WordNet not found. Downloading...")
                nltk.download("wordnet")

            try:
                from nltk.stem import WordNetLemmatizer

                self.lemmatizer = WordNetLemmatizer()
            except ImportError:
                logger.warning(
                    "NLTK WordNetLemmatizer not available. Lemmatization disabled."
                )
                self.transformations.remove("lemmatize")

        # Initialize spaCy
        if "spacy_process" in self.transformations and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(kwargs.get("spacy_model", "en_core_web_sm"))
            except OSError:
                logger.warning(
                    "spaCy model not found. Please install it with: "
                    "python -m spacy download en_core_web_sm"
                )
                self.transformations.remove("spacy_process")
                self.nlp = None
        else:
            self.nlp = None

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        result = text

        # Apply transformations in order
        for transformation in self.transformations:
            transform_method = getattr(self, f"transform_{transformation}", None)
            if transform_method and callable(transform_method):
                result = transform_method(result)
            else:
                logger.warning(f"Unknown transformation: {transformation}")

        return result

    def transform_strip_whitespace(self, text: str) -> str:
        """Strip leading and trailing whitespace.

        Args:
            text: Input text

        Returns:
            Text with leading and trailing whitespace removed
        """
        return text.strip()

    def transform_normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters.

        Args:
            text: Input text

        Returns:
            Text with normalized Unicode
        """
        # Normalize to NFKC form (compatibility decomposition followed by canonical composition)
        return unicodedata.normalize("NFKC", text)

    def transform_normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple whitespace with single space
        return re.sub(r"\s+", " ", text)

    def transform_remove_control_chars(self, text: str) -> str:
        """Remove control characters.

        Args:
            text: Input text

        Returns:
            Text with control characters removed
        """
        # Remove control characters except newlines and tabs
        return "".join(
            c
            for c in text
            if c == "\n" or c == "\t" or not unicodedata.category(c).startswith("C")
        )

    def transform_replace_chars(self, text: str) -> str:
        """Replace special characters with standard ones.

        Args:
            text: Input text

        Returns:
            Text with special characters replaced
        """
        # Replace special characters
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        return text

    def transform_lowercase(self, text: str) -> str:
        """Convert text to lowercase.

        Args:
            text: Input text

        Returns:
            Lowercase text
        """
        return text.lower()

    def transform_remove_punctuation(self, text: str) -> str:
        """Remove punctuation.

        Args:
            text: Input text

        Returns:
            Text with punctuation removed
        """
        # Remove all punctuation
        return "".join(c for c in text if c not in string.punctuation)

    def transform_remove_numbers(self, text: str) -> str:
        """Remove numbers.

        Args:
            text: Input text

        Returns:
            Text with numbers removed
        """
        # Remove all digits
        return "".join(c for c in text if not c.isdigit())

    def transform_remove_stopwords(self, text: str) -> str:
        """Remove stop words.

        Args:
            text: Input text

        Returns:
            Text with stop words removed
        """
        if not NLTK_AVAILABLE:
            logger.warning("NLTK not available. Skipping stop word removal.")
            return text

        try:
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize

            try:
                nltk.data.find("corpora/stopwords")
            except LookupError:
                logger.warning("NLTK stopwords not found. Downloading...")
                nltk.download("stopwords")

            # Get stop words for the current language
            try:
                stops = set(stopwords.words(self.language))
            except OSError:
                logger.warning(
                    f"No stopwords available for {self.language}. Using English."
                )
                stops = set(stopwords.words("english"))

            # Tokenize and filter out stop words
            tokens = word_tokenize(text)
            filtered = [word for word in tokens if word.lower() not in stops]

            # Join back into text
            return " ".join(filtered)
        except Exception as e:
            logger.warning(f"Error removing stopwords: {e}")
            return text

    def transform_lemmatize(self, text: str) -> str:
        """Lemmatize text.

        Args:
            text: Input text

        Returns:
            Lemmatized text
        """
        if not NLTK_AVAILABLE or not hasattr(self, "lemmatizer"):
            logger.warning("NLTK lemmatizer not available. Skipping lemmatization.")
            return text

        try:
            from nltk.tokenize import word_tokenize

            # Tokenize
            tokens = word_tokenize(text)

            # Lemmatize each token
            lemmatized = [self.lemmatizer.lemmatize(word) for word in tokens]

            # Join back into text
            return " ".join(lemmatized)
        except Exception as e:
            logger.warning(f"Error lemmatizing text: {e}")
            return text

    def transform_spacy_process(self, text: str) -> str:
        """Process text with spaCy.

        Args:
            text: Input text

        Returns:
            Processed text
        """
        if not SPACY_AVAILABLE or not self.nlp:
            logger.warning("spaCy not available. Skipping spaCy processing.")
            return text

        try:
            # Process with spaCy
            doc = self.nlp(text)

            # Extract lemmas
            lemmas = [token.lemma_ for token in doc]

            # Join back into text
            return " ".join(lemmas)
        except Exception as e:
            logger.warning(f"Error processing text with spaCy: {e}")
            return text

    def transform_fix_encoding(self, text: str) -> str:
        """Fix common encoding issues.

        Args:
            text: Input text

        Returns:
            Text with encoding issues fixed
        """
        # Handle common encoding issues
        fixed = text

        # Replace common encoding artifacts - using simple replacements
        # Note: We're only handling a subset of common encoding issues with ASCII replacements
        fixed = fixed.replace("Â", " ")
        fixed = fixed.replace("â€™", "'")
        fixed = fixed.replace("â€œ", '"')
        fixed = fixed.replace("â€", '"')

        return fixed

    def transform_remove_urls(self, text: str) -> str:
        """Remove URLs.

        Args:
            text: Input text

        Returns:
            Text with URLs removed
        """
        return self.compiled_patterns["url"].sub("", text)

    def transform_remove_emails(self, text: str) -> str:
        """Remove email addresses.

        Args:
            text: Input text

        Returns:
            Text with email addresses removed
        """
        return self.compiled_patterns["email"].sub("", text)

    def transform_remove_phone_numbers(self, text: str) -> str:
        """Remove phone numbers.

        Args:
            text: Input text

        Returns:
            Text with phone numbers removed
        """
        return self.compiled_patterns["phone"].sub("", text)

    def transform_remove_ssn(self, text: str) -> str:
        """Remove Social Security Numbers.

        Args:
            text: Input text

        Returns:
            Text with SSNs removed
        """
        return self.compiled_patterns["ssn"].sub("", text)

    def transform_remove_credit_cards(self, text: str) -> str:
        """Remove credit card numbers.

        Args:
            text: Input text

        Returns:
            Text with credit card numbers removed
        """
        return self.compiled_patterns["credit_card"].sub("", text)

    def transform_remove_ip_addresses(self, text: str) -> str:
        """Remove IP addresses.

        Args:
            text: Input text

        Returns:
            Text with IP addresses removed
        """
        return self.compiled_patterns["ip_address"].sub("", text)

    def transform_remove_markdown(self, text: str) -> str:
        """Remove Markdown formatting.

        Args:
            text: Input text

        Returns:
            Text with Markdown formatting removed
        """
        # Replace links with their text content
        text = self.compiled_patterns["markdown_links"].sub(r"\1", text)

        # Remove other common markdown formatting
        text = re.sub(r"[*_]{1,2}(.*?)[*_]{1,2}", r"\1", text)  # Bold/Italic
        text = re.sub(r"~{2}(.*?)~{2}", r"\1", text)  # Strikethrough
        text = re.sub(r"#{1,6}\s+", "", text)  # Headers
        text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)  # Code

        return text

    def transform_remove_html(self, text: str) -> str:
        """Remove HTML tags.

        Args:
            text: Input text

        Returns:
            Text with HTML tags removed
        """
        return self.compiled_patterns["html_tags"].sub("", text)

    def transform_fix_line_breaks(self, text: str) -> str:
        """Fix inconsistent line breaks.

        Args:
            text: Input text

        Returns:
            Text with consistent line breaks
        """
        # Normalize line breaks
        text = re.sub(r"\r\n", "\n", text)  # Windows to Unix
        text = re.sub(r"\r", "\n", text)  # Mac to Unix

        # Fix broken sentences at line breaks
        text = re.sub(r"(?<=[a-z,;:])\n(?=[a-z])", " ", text)

        # Remove more than 2 consecutive line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def transform_fix_spacing(self, text: str) -> str:
        """Fix spacing issues.

        Args:
            text: Input text

        Returns:
            Text with fixed spacing
        """
        # Fix spacing around punctuation
        text = re.sub(r"\s+([.,;:!?)])", r"\1", text)  # Remove space before punctuation
        text = re.sub(r"([([])\s+", r"\1", text)  # Remove space after opening brackets

        # Ensure single space after punctuation
        text = re.sub(r"([.,;:!?])\s*(?! )(?=[^\s])", r"\1 ", text)

        return text

    def transform_redact_pii(self, text: str) -> str:
        """Redact personally identifiable information (PII).

        Args:
            text: Input text

        Returns:
            Text with PII redacted
        """
        # Redact email addresses
        text = self.compiled_patterns["email"].sub("[EMAIL]", text)

        # Redact phone numbers
        text = self.compiled_patterns["phone"].sub("[PHONE]", text)

        # Redact SSNs
        text = self.compiled_patterns["ssn"].sub("[SSN]", text)

        # Redact credit card numbers
        text = self.compiled_patterns["credit_card"].sub("[CREDIT_CARD]", text)

        # Redact IP addresses
        text = self.compiled_patterns["ip_address"].sub("[IP_ADDRESS]", text)

        return text

    def transform_extract_text_only(self, text: str) -> str:
        """Extract only alphabetic text.

        Args:
            text: Input text

        Returns:
            Text with only alphabetic characters and whitespace
        """
        # Keep only alphabetic characters and whitespace
        text = "".join(c for c in text if c.isalpha() or c.isspace())

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def add_custom_transformation(
        self, name: str, transformation_function: Callable[[str], str]
    ) -> None:
        """Add a custom transformation function.

        Args:
            name: Name of the transformation
            transformation_function: Function that takes a string and returns a string
        """
        setattr(self, f"transform_{name}", transformation_function)

    def create_pipeline(self, transformations: List[str]) -> Callable[[str], str]:
        """Create a pipeline of transformations.

        Args:
            transformations: List of transformation names

        Returns:
            Function that applies the transformations in sequence
        """

        def pipeline(text: str) -> str:
            result = text
            for transformation in transformations:
                transform_method = getattr(self, f"transform_{transformation}", None)
                if transform_method and callable(transform_method):
                    result = transform_method(result)
                else:
                    logger.warning(f"Unknown transformation: {transformation}")
            return result

        return pipeline


# Global text normalizer instance
_text_normalizer: Optional[TextNormalizer] = None


def get_text_normalizer(
    transformations: Optional[List[str]] = None,
    custom_patterns: Optional[Dict[str, str]] = None,
    custom_replacements: Optional[Dict[str, str]] = None,
    language: str = "en",
    **kwargs: Any,
) -> TextNormalizer:
    """Get text normalizer instance.

    Args:
        transformations: List of transformation names to apply
        custom_patterns: Custom regex patterns for text cleaning
        custom_replacements: Custom character replacements
        language: Language code for language-specific processing
        **kwargs: Additional configuration options

    Returns:
        Text normalizer instance
    """
    global _text_normalizer

    # Create new instance if one doesn't exist or if configuration changed
    if (
        _text_normalizer is None
        or (
            transformations is not None
            and transformations != _text_normalizer.transformations
        )
        or (language != _text_normalizer.language)
    ):
        _text_normalizer = TextNormalizer(
            transformations=transformations,
            custom_patterns=custom_patterns,
            custom_replacements=custom_replacements,
            language=language,
            **kwargs,
        )

    return _text_normalizer
