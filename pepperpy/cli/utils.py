"""Utilities for the Pepperpy CLI.

This module provides utility functions for:
- Console output formatting
- Input validation and parsing
- File and path handling
- Configuration management
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from pepperpy.cli.exceptions import ConfigError, ValidationError

# Configure rich console
console = Console()


def format_error(message: str, hint: Optional[str] = None) -> None:
    """Format and print an error message.

    Args:
        message: The error message to display.
        hint: Optional hint for resolving the error.
    """
    console.print(f"[red]Error:[/red] {message}")
    if hint:
        console.print(f"[yellow]Hint:[/yellow] {hint}")


def format_success(message: str) -> None:
    """Format and print a success message.

    Args:
        message: The success message to display.
    """
    console.print(f"[green]Success:[/green] {message}")


def format_warning(message: str) -> None:
    """Format and print a warning message.

    Args:
        message: The warning message to display.
    """
    console.print(f"[yellow]Warning:[/yellow] {message}")


def format_info(message: str) -> None:
    """Format and print an info message.

    Args:
        message: The info message to display.
    """
    console.print(f"[blue]Info:[/blue] {message}")


def format_code(code: str, language: str = "python") -> None:
    """Format and print code with syntax highlighting.

    Args:
        code: The code to display.
        language: The programming language for syntax highlighting.
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def format_table(
    headers: List[str], rows: List[List[str]], title: Optional[str] = None
) -> None:
    """Format and print data in a table.

    Args:
        headers: The column headers.
        rows: The table rows.
        title: Optional table title.
    """
    table = Table(title=title)
    for header in headers:
        table.add_column(header, style="cyan")
    for row in rows:
        table.add_row(*row)
    console.print(table)


def format_panel(content: str, title: Optional[str] = None) -> None:
    """Format and print content in a panel.

    Args:
        content: The content to display.
        title: Optional panel title.
    """
    panel = Panel(content, title=title)
    console.print(panel)


def validate_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """Validate and convert a path string.

    Args:
        path: The path to validate.
        must_exist: Whether the path must exist.

    Returns:
        The validated Path object.

    Raises:
        ValidationError: If the path is invalid or doesn't exist when required.
    """
    try:
        path_obj = Path(path).resolve()
        if must_exist and not path_obj.exists():
            raise ValidationError("path", str(path), "Path does not exist")
        return path_obj
    except Exception as e:
        raise ValidationError("path", str(path), str(e))


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and validate a JSON configuration file.

    Args:
        config_path: Path to the config file.

    Returns:
        The loaded configuration dictionary.

    Raises:
        ConfigError: If the config file is invalid or cannot be loaded.
    """
    try:
        path_obj = validate_path(config_path)
        with path_obj.open() as f:
            return json.load(f)
    except ValidationError as e:
        raise ConfigError(str(config_path), str(e))
    except json.JSONDecodeError as e:
        raise ConfigError(str(config_path), f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise ConfigError(str(config_path), str(e))


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """Save a configuration dictionary to a JSON file.

    Args:
        config: The configuration dictionary to save.
        config_path: Path to save the config file.

    Raises:
        ConfigError: If the config cannot be saved.
    """
    try:
        path_obj = Path(config_path)
        with path_obj.open("w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise ConfigError(str(config_path), f"Failed to save config: {str(e)}")


def get_config_dir() -> Path:
    """Get the Pepperpy configuration directory.

    Returns:
        Path to the config directory.
    """
    config_dir = Path(click.get_app_dir("pepperpy"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get the Pepperpy data directory.

    Returns:
        Path to the data directory.
    """
    data_dir = Path(os.path.expanduser("~/.local/share/pepperpy"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
