"""Utility functions for formatting data."""

from datetime import datetime
from typing import Optional, Union


def format_date(
    date: Union[str, datetime],
    format_str: Optional[str] = None,
    input_format: Optional[str] = None,
) -> str:
    """Format a date string or datetime object.

    Args:
        date: The date to format.
        format_str: The format string to use for output.
            If None, uses ISO format.
        input_format: The format string to use for parsing the date string.
            Only used if date is a string.

    Returns:
        The formatted date string.

    Raises:
        ValueError: If the date string cannot be parsed.
    """
    if isinstance(date, str):
        if input_format:
            date = datetime.strptime(date, input_format)
        else:
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                try:
                    date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"Could not parse date string: {date}")

    if format_str:
        return date.strftime(format_str)
    else:
        return date.isoformat() 