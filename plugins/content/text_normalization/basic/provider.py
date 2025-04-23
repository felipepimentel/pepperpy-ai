"""Basic text normalizer provider.

This module provides a basic text normalizer implementation with common transformations
that don't require external dependencies.
"""

import re
import string
import unicodedata
from typing import dict, list, set, Optional, Any

from pepperpy.content.base import TextNormalizationError, TextNormalizer
from pepperpy.content import ContentProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.content.base import ContentError
from pepperpy.content.base import ContentError

logger = logger.getLogger(__name__)


class BasicTextNormalizer(class BasicTextNormalizer(TextNormalizer, ProviderPlugin):
    """Basic text normalizer implementation.

    This normalizer provides common text transformations without external dependencies.
    """):
    """
    Content basictextnormalizer provider.
    
    This provider implements basictextnormalizer functionality for the PepperPy content framework.
    """

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

    async def initialize(self) -> None:
 """Initialize the normalizer.

        This method is called automatically when the provider is first used.
 """
        # Initialize state
        self.initialized = True

        # Get configuration
        self.transformations = self.config.get(
            "transformations",
            [
                "strip_whitespace",
                "normalize_unicode",
                "normalize_whitespace",
                "remove_control_chars",
            ],
        )

        # set patterns
        custom_patterns = self.custom_patterns
        self.patterns = self.DEFAULT_PATTERNS.copy()
        self.patterns.update(custom_patterns)

        # set replacements
        custom_replacements = self.custom_replacements
        self.replacements = self.DEFAULT_REPLACEMENTS.copy()
        self.replacements.update(custom_replacements)

        # set language
        self.language = self.config.get("language", "en")

        # Compile patterns
        self.compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self.patterns.items()
        }

        self.logger.debug(
            f"Initialized with {len(self.transformations)} transformations, language={self.language}"
        )

    async def cleanup(self) -> None:
 """Clean up resources.

        This method is called automatically when the context manager exits.
 """
        # No resources to clean up
        self.compiled_patterns = {}
        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute text normalization task.

        Args:
            input_data: Input data containing:
                - text: Text to normalize
                - transformations: (Optional) list of transformations to apply

        Returns:
            dict with normalized text
        """
        text = input_data.get("text", "")
        if not text:
            raise ContentError("No text provided")

        # Check if we should override default transformations
        override_transformations = input_data.get("transformations")
        if override_transformations:
            temp_transformations = self.transformations
            self.transformations = override_transformations

        try:
            normalized_text = self.normalize(text)

            # Restore original transformations if overridden
            if override_transformations:
                self.transformations = temp_transformations

            return {
                "status": "success",
                "normalized_text": normalized_text,
                "transformations_applied": self.transformations,
            }
        except Exception as e:
            self.logger.error(f"Normalization error: {e}")

            # Restore original transformations if overridden
            if override_transformations:
                self.transformations = temp_transformations

            raise ContentError(str(e))

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text

        Raises:
            TextNormalizationError: If normalization fails
        """
        if not text:
            return ""

        if not self.initialized:
            raise TextNormalizationError("Normalizer not initialized")

        result = text

        # Apply transformations in order
        for transformation in self.transformations:
            transform_method = getattr(self, f"transform_{transformation}", None)
            if transform_method and callable(transform_method):
                try:
                    result = transform_method(result)
                except Exception as e:
                    self.logger.error(f"Error in {transformation}: {e}")
                    raise TextNormalizationError(f"Error in {transformation}: {e}")
            else:
                self.logger.warning(f"Unknown transformation: {transformation}")

        return result

    def transform_strip_whitespace(self, text: str) -> str:


    """Strip leading and trailing whitespace.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return text.strip()

    def transform_normalize_unicode(self, text: str) -> str:


    """Normalize Unicode characters to NFKC form.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return unicodedata.normalize("NFKC", text)

    def transform_normalize_whitespace(self, text: str) -> str:


    """Replace multiple whitespace with single space.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return re.sub(r"\s+", " ", text)

    def transform_remove_control_chars(self, text: str) -> str:


    """Remove control characters except newlines and tabs.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return "".join(
            c
            for c in text
            if c == "\n" or c == "\t" or not unicodedata.category(c).startswith("C")
        )

    def transform_replace_chars(self, text: str) -> str:


    """Replace special characters with standard ones.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        return text

    def transform_lowercase(self, text: str) -> str:


    """Convert text to lowercase.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return text.lower()

    def transform_remove_punctuation(self, text: str) -> str:


    """Remove all punctuation.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return "".join(c for c in text if c not in string.punctuation)

    def transform_remove_numbers(self, text: str) -> str:


    """Remove all digits.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return "".join(c for c in text if not c.isdigit())

    def transform_fix_encoding(self, text: str) -> str:


    """Fix common encoding issues.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        fixed = text
        fixed = fixed.replace("Â", " ")
        fixed = fixed.replace("â€™", "'")
        fixed = fixed.replace("â€œ", '"')
        fixed = fixed.replace("â€", '"')
        fixed = fixed.replace("é", "e")
        fixed = fixed.replace("è", "e")
        fixed = fixed.replace("à", "a")
        fixed = fixed.replace("ù", "u")
        fixed = fixed.replace("ç", "c")
        return fixed

    def transform_remove_urls(self, text: str) -> str:


    """Remove URLs.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["url"].sub("", text)

    def transform_remove_emails(self, text: str) -> str:


    """Remove email addresses.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["email"].sub("", text)

    def transform_remove_phone_numbers(self, text: str) -> str:


    """Remove phone numbers.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["phone"].sub("", text)

    def transform_remove_ssn(self, text: str) -> str:


    """Remove Social Security Numbers.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["ssn"].sub("", text)

    def transform_remove_credit_cards(self, text: str) -> str:


    """Remove credit card numbers.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["credit_card"].sub("", text)

    def transform_remove_ip_addresses(self, text: str) -> str:


    """Remove IP addresses.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["ip_address"].sub("", text)

    def transform_remove_markdown(self, text: str) -> str:


    """Remove Markdown formatting.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        text = self.compiled_patterns["markdown_links"].sub(r"\1", text)
        text = re.sub(r"[*_]{1,2}(.*?)[*_]{1,2}", r"\1", text)  # Bold/Italic
        text = re.sub(r"~{2}(.*?)~{2}", r"\1", text)  # Strikethrough
        text = re.sub(r"#{1,6}\s+", "", text)  # Headers
        text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)  # Code
        return text

    def transform_remove_html(self, text: str) -> str:


    """Remove HTML tags.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        return self.compiled_patterns["html_tags"].sub("", text)

    def transform_fix_line_breaks(self, text: str) -> str:


    """Fix inconsistent line breaks.



    Args:


        text: Parameter description



    Returns:


        Return description


    """
        text = re.sub(r"\r\n", "\n", text)  # Windows to Unix
        text = re.sub(r"\r", "\n", text)  # Mac to Unix
        text = re.sub(r"(?<=[a-z,;:])\n(?=[a-z])", " ", text)  # Fix broken sentences
        text = re.sub(r"\n{3,}", "\n\n", text)  # Remove excess breaks
        return text
