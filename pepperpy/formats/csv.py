"""CSV format handling functionality.

This module provides functionality for processing and transforming CSV content,
including parsing, formatting, and validation.
"""

import csv
import io
from typing import Any, Dict, List, Optional

from pepperpy.core.common.errors.base import PepperError


class ProcessingError(PepperError):
    """Error raised when processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details if details is not None else {})


class CSVProcessor:
    """Process and transform CSV content."""

    def __init__(self, delimiter: str = ",", quotechar: str = '"'):
        """Initialize CSV processor.

        Args:
            delimiter: CSV delimiter character
            quotechar: CSV quote character
        """
        self.delimiter = delimiter
        self.quotechar = quotechar

    def parse(self, content: str) -> List[Dict[str, str]]:
        """Parse CSV content into a list of dictionaries.

        Args:
            content: CSV content to parse

        Returns:
            List of dictionaries representing CSV rows

        Raises:
            ProcessingError: If parsing fails
        """
        try:
            reader = csv.DictReader(
                io.StringIO(content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            return list(reader)
        except Exception as e:
            raise ProcessingError(f"CSV parsing failed: {str(e)}") from e

    def format(self, data: List[Dict[str, Any]]) -> str:
        """Format data as CSV.

        Args:
            data: List of dictionaries to format as CSV

        Returns:
            Formatted CSV content

        Raises:
            ProcessingError: If formatting fails
        """
        if not data:
            return ""

        try:
            output = io.StringIO()
            fieldnames = data[0].keys()
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        except Exception as e:
            raise ProcessingError(f"CSV formatting failed: {str(e)}") from e

    def validate(self, content: str) -> List[str]:
        """Validate CSV content.

        Args:
            content: CSV content to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not content:
            errors.append("Empty content")
            return errors

        try:
            # Check if CSV can be parsed
            reader = csv.reader(
                io.StringIO(content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            rows = list(reader)

            if not rows:
                errors.append("CSV has no rows")
            elif len(rows) == 1:
                errors.append("CSV has only a header row")
            else:
                # Check if all rows have the same number of columns
                header_length = len(rows[0])
                for i, row in enumerate(rows[1:], 2):
                    if len(row) != header_length:
                        errors.append(
                            f"Row {i} has {len(row)} columns, expected {header_length}"
                        )

        except Exception as e:
            errors.append(f"CSV validation failed: {str(e)}")

        return errors
