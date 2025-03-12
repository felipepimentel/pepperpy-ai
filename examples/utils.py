#!/usr/bin/env python
"""Utility functions for PepperPy examples.

This module provides common utility functions used across the PepperPy examples:
- Environment variable loading
- API key validation
- Logging setup

These utilities help standardize the setup process for all examples and
reduce code duplication.

Requirements:
    - Python 3.9+
    - python-dotenv

Usage:
    from utils import load_env, check_api_keys

    # Load environment variables
    load_env()

    # Check for required API keys
    check_api_keys(["OPENAI_API_KEY"])
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def load_env(env_file: str = ".env") -> None:
    """Load environment variables from a .env file.

    This function attempts to load environment variables from a .env file
    if it exists. It uses python-dotenv if available, otherwise it implements
    a simple fallback parser.

    Args:
        env_file: Path to the .env file, relative to the current directory.
                  Defaults to ".env".
    """
    # Check if the .env file exists
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"No {env_file} file found. Using existing environment variables.")
        return

    try:
        # Try to use python-dotenv if available
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
            print(f"Loaded environment variables from {env_file} using python-dotenv")
        except ImportError:
            # Simple fallback implementation if python-dotenv is not available
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    # Parse key-value pairs
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # Set environment variable
                        os.environ[key] = value
            print(f"Loaded environment variables from {env_file} using fallback parser")
    except Exception as e:
        print(f"Error loading environment variables: {e}")


def check_api_keys(
    required_keys: Dict[str, str], optional_keys: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Check if required API keys are set in environment variables.

    This function checks if the required API keys are set in the environment
    variables. It prints a message for each key indicating whether it's available
    or missing. For required keys, it will exit the program if any are missing.
    For optional keys, it will just print a warning.

    Args:
        required_keys: Dictionary mapping environment variable names to descriptions
                       of what they're used for.
        optional_keys: Dictionary mapping optional environment variable names to
                       descriptions of what they're used for.

    Returns:
        Dictionary containing the available API keys and their values.

    Raises:
        SystemExit: If any required API keys are missing.
    """
    available_keys = {}
    missing_required = False

    # Check required keys
    print("\nChecking required API keys:")
    for key, description in required_keys.items():
        value = os.environ.get(key)
        if value:
            print(f"✅ {key}: Available (required for {description})")
            available_keys[key] = value
        else:
            print(f"❌ {key}: Missing (required for {description})")
            missing_required = True

    # Check optional keys if provided
    if optional_keys:
        print("\nChecking optional API keys:")
        for key, description in optional_keys.items():
            value = os.environ.get(key)
            if value:
                print(f"✅ {key}: Available (used for {description})")
                available_keys[key] = value
            else:
                print(f"ℹ️ {key}: Missing (optional for {description})")

    # Exit if any required keys are missing
    if missing_required:
        print(
            "\n❌ Error: Missing required API keys. Please set them in your environment or .env file."
        )
        print("Example .env file format:")
        for key in required_keys:
            print(f"{key}=your_{key.lower()}_here")
        sys.exit(1)

    print()  # Add a blank line for readability
    return available_keys


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """Set up logging configuration for examples.

    This function configures the Python logging system with sensible defaults
    for the examples. It sets up console logging and optionally file logging.

    Args:
        level: The logging level to use. Defaults to logging.INFO.
        log_file: Path to a log file. If provided, logs will be written to this file
                  in addition to the console.
        log_format: Custom log format string. If not provided, a default format is used.
    """
    # Default log format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Create file handler if log_file is provided
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)
            print(f"Logging to file: {log_file}")
        except Exception as e:
            print(f"Error setting up file logging: {e}")

    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.debug("Logging setup complete")


def create_example_env_file() -> None:
    """Create an example .env file if one doesn't exist.

    This function creates a template .env file with placeholders for
    common API keys used in the examples.
    """
    if not os.path.exists(".env.example"):
        with open(".env.example", "w") as f:
            f.write("""# PepperPy Example Environment Variables
# Copy this file to .env and fill in your API keys

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Anthropic API Key
ANTHROPIC_API_KEY=sk-...

# Cohere API Key
COHERE_API_KEY=co-...

# Other provider keys can be added as needed
""")
        print("Created .env.example file")


if __name__ == "__main__":
    # Example usage
    load_env()
    setup_logging(level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.info("Testing utility functions")

    required_keys = {"EXAMPLE_API_KEY": "Example functionality"}
    optional_keys = {"OPTIONAL_API_KEY": "Optional functionality"}

    try:
        available_keys = check_api_keys(required_keys, optional_keys)
        logger.info(f"Available keys: {list(available_keys.keys())}")
    except SystemExit:
        logger.error("API key check failed")
