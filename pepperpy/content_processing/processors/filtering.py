"""Document filtering for document processing.

This module provides functionality for filtering documents based on
content, metadata, or structural features.
"""

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)


class FilterType(str, Enum):
    """Types of document filters."""

    CONTENT = "content"  # Filter based on document content
    METADATA = "metadata"  # Filter based on document metadata
    EXTENSION = "extension"  # Filter based on file extension
    SIZE = "size"  # Filter based on file size
    DATE = "date"  # Filter based on file date


class FilterOperator(str, Enum):
    """Operators for filter conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    REGEX = "regex"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class DocumentFilterError(PepperpyError):
    """Error raised during document filtering operations."""

    pass


class FilterCondition:
    """Condition for document filtering."""

    def __init__(
        self,
        filter_type: FilterType,
        field: Optional[str] = None,
        operator: FilterOperator = FilterOperator.EQUALS,
        value: Any = None,
        case_sensitive: bool = False,
    ) -> None:
        """Initialize filter condition.

        Args:
            filter_type: Type of filter
            field: Field to filter on (e.g., metadata field, content section)
            operator: Filtering operator
            value: Value to compare against
            case_sensitive: Whether string comparisons are case sensitive
        """
        self.filter_type = filter_type
        self.field = field
        self.operator = operator
        self.value = value
        self.case_sensitive = case_sensitive

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter condition to dictionary."""
        return {
            "type": self.filter_type,
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "case_sensitive": self.case_sensitive,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterCondition":
        """Create filter condition from dictionary.

        Args:
            data: Dictionary with filter condition data

        Returns:
            Filter condition instance
        """
        return cls(
            filter_type=FilterType(data.get("type", FilterType.CONTENT)),
            field=data.get("field"),
            operator=FilterOperator(data.get("operator", FilterOperator.EQUALS)),
            value=data.get("value"),
            case_sensitive=data.get("case_sensitive", False),
        )

    def __str__(self) -> str:
        """String representation of filter condition."""
        return f"{self.filter_type}:{self.field} {self.operator} {self.value}"


class DocumentFilter:
    """Filter for document processing.

    This class provides functionality for filtering documents based on
    various criteria such as content, metadata, or file properties.
    """

    def __init__(
        self,
        conditions: Optional[List[FilterCondition]] = None,
        match_all: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize document filter.

        Args:
            conditions: List of filter conditions
            match_all: Whether all conditions must match (AND) or just one (OR)
            **kwargs: Additional configuration options
        """
        self.conditions = conditions or []
        self.match_all = match_all
        self.config = kwargs

    def add_condition(self, condition: FilterCondition) -> None:
        """Add a filter condition.

        Args:
            condition: Filter condition to add
        """
        self.conditions.append(condition)

    def add_content_filter(
        self,
        text: str,
        operator: FilterOperator = FilterOperator.CONTAINS,
        section: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> None:
        """Add a content-based filter.

        Args:
            text: Text to find in document
            operator: How to match the text
            section: Specific section to search in (if applicable)
            case_sensitive: Whether matching is case sensitive
        """
        condition = FilterCondition(
            filter_type=FilterType.CONTENT,
            field=section,
            operator=operator,
            value=text,
            case_sensitive=case_sensitive,
        )
        self.add_condition(condition)

    def add_metadata_filter(
        self,
        field: str,
        value: Any,
        operator: FilterOperator = FilterOperator.EQUALS,
        case_sensitive: bool = False,
    ) -> None:
        """Add a metadata-based filter.

        Args:
            field: Metadata field to filter on
            value: Value to compare against
            operator: How to compare values
            case_sensitive: Whether string matching is case sensitive
        """
        condition = FilterCondition(
            filter_type=FilterType.METADATA,
            field=field,
            operator=operator,
            value=value,
            case_sensitive=case_sensitive,
        )
        self.add_condition(condition)

    def add_extension_filter(
        self, extensions: Union[str, List[str]], include: bool = True
    ) -> None:
        """Add an extension-based filter.

        Args:
            extensions: File extension(s) to filter
            include: True to include these extensions, False to exclude
        """
        if isinstance(extensions, str):
            extensions = [extensions]

        # Ensure extensions start with a dot
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]

        condition = FilterCondition(
            filter_type=FilterType.EXTENSION,
            operator=FilterOperator.CONTAINS
            if include
            else FilterOperator.NOT_CONTAINS,
            value=extensions,
        )
        self.add_condition(condition)

    def add_size_filter(
        self, size: int, operator: FilterOperator = FilterOperator.LESS_THAN
    ) -> None:
        """Add a size-based filter.

        Args:
            size: File size in bytes
            operator: How to compare size (greater_than, less_than)
        """
        if operator not in (FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN):
            raise DocumentFilterError(
                f"Invalid operator for size filter: {operator}, "
                f"must be greater_than or less_than"
            )

        condition = FilterCondition(
            filter_type=FilterType.SIZE, operator=operator, value=size
        )
        self.add_condition(condition)

    def add_date_filter(
        self, date: str, operator: FilterOperator = FilterOperator.GREATER_THAN
    ) -> None:
        """Add a date-based filter.

        Args:
            date: Date string in ISO format (YYYY-MM-DD)
            operator: How to compare dates (greater_than, less_than)
        """
        if operator not in (FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN):
            raise DocumentFilterError(
                f"Invalid operator for date filter: {operator}, "
                f"must be greater_than or less_than"
            )

        condition = FilterCondition(
            filter_type=FilterType.DATE, operator=operator, value=date
        )
        self.add_condition(condition)

    def evaluate_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate a single filter condition against a document.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        # Handle different filter types
        if condition.filter_type == FilterType.CONTENT:
            return self._evaluate_content_condition(condition, document)
        elif condition.filter_type == FilterType.METADATA:
            return self._evaluate_metadata_condition(condition, document)
        elif condition.filter_type == FilterType.EXTENSION:
            return self._evaluate_extension_condition(condition, document)
        elif condition.filter_type == FilterType.SIZE:
            return self._evaluate_size_condition(condition, document)
        elif condition.filter_type == FilterType.DATE:
            return self._evaluate_date_condition(condition, document)
        else:
            logger.warning(f"Unknown filter type: {condition.filter_type}")
            return False

    def _evaluate_content_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate a content-based filter condition.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        # Get document content
        content = document.get("content", "")
        if not content:
            return False

        # Check specific section if specified
        if condition.field:
            # Get section content if available
            sections = document.get("sections", {})
            if not sections:
                return False

            section_content = sections.get(condition.field, "")
            if not section_content:
                return False

            content = section_content

        # Get comparison value
        value = condition.value
        if not condition.case_sensitive and isinstance(value, str):
            content = content.lower()
            value = value.lower()

        # Apply operator
        if condition.operator == FilterOperator.CONTAINS:
            return value in content
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            return value not in content
        elif condition.operator == FilterOperator.EQUALS:
            return content == value
        elif condition.operator == FilterOperator.NOT_EQUALS:
            return content != value
        elif condition.operator == FilterOperator.REGEX:
            try:
                flags = 0 if condition.case_sensitive else re.IGNORECASE
                return bool(re.search(value, content, flags))
            except re.error:
                logger.warning(f"Invalid regular expression: {value}")
                return False
        else:
            logger.warning(f"Unsupported operator for content: {condition.operator}")
            return False

    def _evaluate_metadata_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate a metadata-based filter condition.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        if not condition.field:
            logger.warning("Metadata filter requires a field name")
            return False

        # Get document metadata
        metadata = document.get("metadata", {})
        if not metadata:
            return False

        # Check if the field exists
        if condition.operator == FilterOperator.EXISTS:
            return condition.field in metadata
        elif condition.operator == FilterOperator.NOT_EXISTS:
            return condition.field not in metadata

        # Field must exist for other operators
        if condition.field not in metadata:
            return False

        # Get field value
        field_value = metadata[condition.field]
        value = condition.value

        # Handle case sensitivity for strings
        if (
            not condition.case_sensitive
            and isinstance(field_value, str)
            and isinstance(value, str)
        ):
            field_value = field_value.lower()
            value = value.lower()

        # Apply operator
        if condition.operator == FilterOperator.EQUALS:
            return field_value == value
        elif condition.operator == FilterOperator.NOT_EQUALS:
            return field_value != value
        elif condition.operator == FilterOperator.CONTAINS:
            if isinstance(field_value, str):
                return value in field_value
            elif isinstance(field_value, (list, tuple, set)):
                return value in field_value
            else:
                return False
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            if isinstance(field_value, str):
                return value not in field_value
            elif isinstance(field_value, (list, tuple, set)):
                return value not in field_value
            else:
                return False
        elif condition.operator == FilterOperator.GREATER_THAN:
            if not isinstance(field_value, (int, float)) or not isinstance(
                value, (int, float)
            ):
                try:
                    # Try to convert to numbers
                    field_value = float(field_value)
                    value = float(value)
                except (ValueError, TypeError):
                    return False
            return field_value > value
        elif condition.operator == FilterOperator.LESS_THAN:
            if not isinstance(field_value, (int, float)) or not isinstance(
                value, (int, float)
            ):
                try:
                    # Try to convert to numbers
                    field_value = float(field_value)
                    value = float(value)
                except (ValueError, TypeError):
                    return False
            return field_value < value
        elif condition.operator == FilterOperator.REGEX:
            if not isinstance(field_value, str):
                return False
            try:
                flags = 0 if condition.case_sensitive else re.IGNORECASE
                return bool(re.search(value, field_value, flags))
            except re.error:
                logger.warning(f"Invalid regular expression: {value}")
                return False
        else:
            logger.warning(f"Unsupported operator for metadata: {condition.operator}")
            return False

    def _evaluate_extension_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate an extension-based filter condition.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        # Get document file path
        path = document.get("path", "")
        if not path:
            return False

        # Get file extension
        extension = Path(path).suffix.lower()

        # Get extension list from condition
        extensions = condition.value
        if isinstance(extensions, str):
            extensions = [extensions]

        # Apply operator
        if condition.operator == FilterOperator.CONTAINS:
            return extension in extensions
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            return extension not in extensions
        else:
            logger.warning(f"Unsupported operator for extension: {condition.operator}")
            return False

    def _evaluate_size_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate a size-based filter condition.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        # Get document size
        size = document.get("size", 0)
        if not isinstance(size, (int, float)):
            try:
                size = int(size)
            except (ValueError, TypeError):
                return False

        # Get comparison value
        value = condition.value
        if not isinstance(value, (int, float)):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return False

        # Apply operator
        if condition.operator == FilterOperator.GREATER_THAN:
            return size > value
        elif condition.operator == FilterOperator.LESS_THAN:
            return size < value
        elif condition.operator == FilterOperator.EQUALS:
            return size == value
        else:
            logger.warning(f"Unsupported operator for size: {condition.operator}")
            return False

    def _evaluate_date_condition(
        self, condition: FilterCondition, document: Dict[str, Any]
    ) -> bool:
        """Evaluate a date-based filter condition.

        Args:
            condition: Filter condition to evaluate
            document: Document data to evaluate against

        Returns:
            True if the condition matches, False otherwise
        """
        import datetime

        # Get document date
        date_str = document.get("date")
        if not date_str:
            # Try to get date from metadata
            metadata = document.get("metadata", {})
            date_str = (
                metadata.get("date")
                or metadata.get("created")
                or metadata.get("modified")
            )

        if not date_str:
            return False

        # Parse document date
        try:
            if isinstance(date_str, datetime.datetime):
                doc_date = date_str
            else:
                doc_date = datetime.datetime.fromisoformat(
                    str(date_str).replace("Z", "+00:00")
                )
        except (ValueError, TypeError):
            try:
                # Try to parse with dateutil
                from dateutil import parser

                doc_date = parser.parse(str(date_str))
            except (ImportError, ValueError, TypeError):
                return False

        # Parse condition date
        condition_date_str = condition.value
        try:
            if isinstance(condition_date_str, datetime.datetime):
                condition_date = condition_date_str
            else:
                condition_date = datetime.datetime.fromisoformat(
                    str(condition_date_str).replace("Z", "+00:00")
                )
        except (ValueError, TypeError):
            try:
                # Try to parse with dateutil
                from dateutil import parser

                condition_date = parser.parse(str(condition_date_str))
            except (ImportError, ValueError, TypeError):
                return False

        # Apply operator
        if condition.operator == FilterOperator.GREATER_THAN:
            return doc_date > condition_date
        elif condition.operator == FilterOperator.LESS_THAN:
            return doc_date < condition_date
        elif condition.operator == FilterOperator.EQUALS:
            return doc_date.date() == condition_date.date()
        else:
            logger.warning(f"Unsupported operator for date: {condition.operator}")
            return False

    def matches(self, document: Dict[str, Any]) -> bool:
        """Check if a document matches the filter.

        Args:
            document: Document data to check

        Returns:
            True if the document matches the filter, False otherwise
        """
        if not self.conditions:
            return True

        results = [
            self.evaluate_condition(condition, document)
            for condition in self.conditions
        ]

        if self.match_all:
            return all(results)
        else:
            return any(results)

    def filter_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of documents.

        Args:
            documents: List of document data dictionaries

        Returns:
            Filtered list of documents
        """
        return [doc for doc in documents if self.matches(doc)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary."""
        return {
            "conditions": [condition.to_dict() for condition in self.conditions],
            "match_all": self.match_all,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentFilter":
        """Create filter from dictionary.

        Args:
            data: Dictionary with filter data

        Returns:
            Document filter instance
        """
        conditions = [
            FilterCondition.from_dict(condition)
            for condition in data.get("conditions", [])
        ]
        match_all = data.get("match_all", True)
        return cls(conditions=conditions, match_all=match_all)


class SectionExtractor:
    """Extractor for document sections.

    This class provides functionality for extracting logical sections from
    document content, such as paragraphs, headings, tables, etc.
    """

    def __init__(
        self,
        heading_patterns: Optional[Dict[str, str]] = None,
        section_patterns: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize section extractor.

        Args:
            heading_patterns: Dictionary of heading regex patterns
            section_patterns: Dictionary of section regex patterns
            **kwargs: Additional configuration options
        """
        # Default heading patterns
        self.heading_patterns = {
            "h1": r"^#\s+(.+)$",
            "h2": r"^##\s+(.+)$",
            "h3": r"^###\s+(.+)$",
            "h4": r"^####\s+(.+)$",
            "h5": r"^#####\s+(.+)$",
            "h6": r"^######\s+(.+)$",
            "title": r"^(.+)\n[=]{2,}$",
            "subtitle": r"^(.+)\n[-]{2,}$",
        }
        if heading_patterns:
            self.heading_patterns.update(heading_patterns)

        # Default section patterns
        self.section_patterns = {
            "code_block": r"```[\s\S]*?```",
            "table": r"\|.+\|\n\|[-:]+\|[-:]+\|[\s\S]*?(?:\n\n|\Z)",
            "list": r"(?:^[*+-]\s+.*\n)+",
            "numbered_list": r"(?:^\d+\.\s+.*\n)+",
            "blockquote": r"(?:^>\s+.*\n)+",
        }
        if section_patterns:
            self.section_patterns.update(section_patterns)

        # Compile patterns
        self.compiled_heading_patterns = {
            name: re.compile(pattern, re.MULTILINE)
            for name, pattern in self.heading_patterns.items()
        }
        self.compiled_section_patterns = {
            name: re.compile(pattern, re.MULTILINE)
            for name, pattern in self.section_patterns.items()
        }

        # Storage for extracted sections
        self.config = kwargs

    def extract_sections(self, text: str) -> Dict[str, Any]:
        """Extract sections from document text.

        Args:
            text: Document text

        Returns:
            Dictionary of sections
        """
        if not text:
            return {}

        # Find all headings with their positions
        headings = []
        for name, pattern in self.compiled_heading_patterns.items():
            for match in pattern.finditer(text):
                headings.append({
                    "type": name,
                    "title": match.group(1).strip()
                    if match.groups()
                    else match.group(0).strip(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # Sort headings by position
        headings.sort(key=lambda h: h["start"])

        # Extract content between headings
        sections = {}
        for i, heading in enumerate(headings):
            section_name = heading["title"]
            section_type = heading["type"]
            start = heading["end"]
            end = headings[i + 1]["start"] if i + 1 < len(headings) else len(text)

            # Extract section content
            section_content = text[start:end].strip()

            # Store section
            sections[section_name] = {
                "content": section_content,
                "type": section_type,
                "metadata": {
                    "start": start,
                    "end": end,
                    "length": len(section_content),
                },
            }

        # If no headings found, treat entire document as a single section
        if not headings:
            sections["main"] = {
                "content": text.strip(),
                "type": "document",
                "metadata": {
                    "start": 0,
                    "end": len(text),
                    "length": len(text),
                },
            }

        # Find special section types (tables, code blocks, etc.)
        special_sections = {}
        for name, pattern in self.compiled_section_patterns.items():
            for i, match in enumerate(pattern.finditer(text)):
                section_name = f"{name}_{i + 1}"
                special_sections[section_name] = {
                    "content": match.group(0).strip(),
                    "type": name,
                    "metadata": {
                        "start": match.start(),
                        "end": match.end(),
                        "length": len(match.group(0)),
                    },
                }

        # Merge sections
        all_sections = {**sections, **special_sections}

        # Add flat content for convenience in filtering
        section_contents = {
            name: section["content"] for name, section in all_sections.items()
        }

        return {
            "sections": all_sections,
            "section_contents": section_contents,
            "headings": [h["title"] for h in headings],
        }

    def extract_section_by_name(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section by name.

        Args:
            text: Document text
            section_name: Name of the section to extract

        Returns:
            Section content or None if not found
        """
        sections = self.extract_sections(text)
        if not sections:
            return None

        section = sections.get("sections", {}).get(section_name)
        if section:
            return section.get("content")

        return None

    def extract_section_by_type(
        self, text: str, section_type: str
    ) -> List[Dict[str, Any]]:
        """Extract all sections of a specific type.

        Args:
            text: Document text
            section_type: Type of sections to extract

        Returns:
            List of sections matching the type
        """
        sections = self.extract_sections(text)
        if not sections:
            return []

        matching_sections = []
        for name, section in sections.get("sections", {}).items():
            if section.get("type") == section_type:
                matching_sections.append({
                    "name": name,
                    "content": section.get("content", ""),
                    "metadata": section.get("metadata", {}),
                })

        return matching_sections


# Global section extractor instance
_section_extractor: Optional[SectionExtractor] = None


def get_section_extractor(
    heading_patterns: Optional[Dict[str, str]] = None,
    section_patterns: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> SectionExtractor:
    """Get section extractor instance.

    Args:
        heading_patterns: Dictionary of heading regex patterns
        section_patterns: Dictionary of section regex patterns
        **kwargs: Additional configuration options

    Returns:
        Section extractor instance
    """
    global _section_extractor

    if _section_extractor is None:
        _section_extractor = SectionExtractor(
            heading_patterns=heading_patterns,
            section_patterns=section_patterns,
            **kwargs,
        )

    return _section_extractor
