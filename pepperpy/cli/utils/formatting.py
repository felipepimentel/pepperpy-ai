"""Formatting utilities for CLI output.

This module provides utilities for formatting CLI output using Rich.
"""

from typing import Any, List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Configure rich console
console = Console()


def format_success(message: str) -> Text:
    """Format a success message.

    Args:
        message: Success message

    Returns:
        Formatted text
    """
    return Text(message, style="green bold")


def format_error(message: str) -> Text:
    """Format an error message.

    Args:
        message: Error message

    Returns:
        Formatted text
    """
    return Text(message, style="red bold")


def format_warning(message: str) -> Text:
    """Format a warning message.

    Args:
        message: Warning message

    Returns:
        Formatted text
    """
    return Text(message, style="yellow bold")


def format_info(message: str) -> Text:
    """Format an info message.

    Args:
        message: Info message

    Returns:
        Formatted text
    """
    return Text(message, style="blue")


def format_panel(
    content: Union[str, Text],
    title: Optional[str] = None,
    style: str = "none",
) -> Panel:
    """Format content in a panel.

    Args:
        content: Panel content
        title: Panel title
        style: Panel style

    Returns:
        Formatted panel
    """
    return Panel(content, title=title, style=style)


def format_table(
    columns: List[str],
    rows: List[List[Any]],
    title: Optional[str] = None,
) -> Table:
    """Format data as a table.

    Args:
        columns: Column names
        rows: Table rows
        title: Table title

    Returns:
        Formatted table
    """
    table = Table(title=title)

    # Add columns
    for column in columns:
        table.add_column(column)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success message
    """
    console.print(format_success(message))


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Error message
    """
    console.print(format_error(message))


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Warning message
    """
    console.print(format_warning(message))


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: Info message
    """
    console.print(format_info(message))
