"""Exceptions utilities module."""

import traceback


def format_exception(error: Exception) -> str:
    """Format an exception with traceback.

    Args:
        error: The exception to format.

    Returns:
        The formatted exception traceback.
    """
    return "".join(traceback.format_exception(type(error), error, error.__traceback__))
