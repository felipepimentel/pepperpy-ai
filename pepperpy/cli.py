"""PepperPy CLI Module.

This module provides the command-line interface for the PepperPy framework.
It includes commands for managing PepperPy projects and applications.
"""

import argparse
import datetime
import importlib
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type

from pepperpy.core.logging import configure_logging, get_logger

# Configure logging
configure_logging(level=os.environ.get("PEPPERPY_LOG_LEVEL", "INFO"))

# Logger for this module
logger = get_logger(__name__)

# Command registry
COMMANDS: Dict[str, Type["Command"]] = {}


def register_command(cls: Type["Command"]) -> Type["Command"]:
    """Register a command class.

    Args:
        cls: The command class to register

    Returns:
        The command class (for decorator usage)
    """
    COMMANDS[cls.name] = cls
    return cls


class Command(ABC):
    """Base class for CLI commands."""

    name: str = ""
    description: str = ""
    help: str = ""

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to
        """
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: The parsed command-line arguments

        Returns:
            The exit code (0 for success, non-zero for failure)
        """
        pass


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        The argument parser
    """
    # Create the main parser
    parser = argparse.ArgumentParser(
        prog="pepperpy",
        description="PepperPy CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add global arguments
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("PEPPERPY_LOG_LEVEL", "INFO"),
        help="Set the log level",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Command to execute",
    )
    subparsers.required = True

    # Add command subparsers
    for command_name, command_cls in COMMANDS.items():
        command_parser = subparsers.add_parser(
            command_name,
            help=command_cls.help,
            description=command_cls.description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        command_instance = command_cls()
        command_instance.add_arguments(command_parser)

    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """Run the CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Configure logging
    configure_logging(level=parsed_args.log_level)

    # Get the command
    command_name = parsed_args.command
    command_cls = COMMANDS.get(command_name)

    if not command_cls:
        logger.error(f"Unknown command: {command_name}")
        parser.print_help()
        return 1

    # Create and execute the command
    try:
        command_instance = command_cls()
        return command_instance.execute(parsed_args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Error executing command {command_name}: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    return run_cli()


# Templates for project files
TEMPLATES: Dict[str, str] = {
    "README.md": """# {project_name}

A PepperPy project.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m {package_name}
```
""",
    "pyproject.toml": """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "{project_description}"
authors = [
    {{name = "{author_name}", email = "{author_email}"}}
]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    "pepperpy",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "black",
    "isort",
    "mypy",
    "flake8",
]

[tool.black]
line-length = 88
target-version = ["py38"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
""",
    "LICENSE": """MIT License

Copyright (c) {year} {author_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    "{package_name}/__init__.py": """\"\"\"
{project_name}

{project_description}
\"\"\"

__version__ = "0.1.0"
""",
    "{package_name}/__main__.py": """\"\"\"Main entry point for the package.\"\"\"

from {package_name}.app import main

if __name__ == "__main__":
    main()
""",
    "{package_name}/app.py": """\"\"\"Main application module.\"\"\"

import pepperpy


def main() -> None:
    \"\"\"Run the application.\"\"\"
    print("Hello from {project_name}!")


def run() -> None:
    \"\"\"Run the application (for use with the pepperpy CLI).\"\"\"
    main()


if __name__ == "__main__":
    main()
""",
    "tests/__init__.py": "",
    "tests/test_app.py": """\"\"\"Tests for the app module.\"\"\"

from {package_name} import app


def test_app() -> None:
    \"\"\"Test that the app module exists.\"\"\"
    assert app is not None
""",
}


@register_command
class InitCommand(Command):
    """Command to initialize a new PepperPy project."""

    name = "init"
    description = "Initialize a new PepperPy project"
    help = "Create a new PepperPy project with the recommended structure"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to
        """
        parser.add_argument(
            "project_name",
            help="Name of the project",
        )

        parser.add_argument(
            "--description",
            default="A PepperPy project",
            help="Description of the project",
        )

        parser.add_argument(
            "--author",
            default="",
            help="Author of the project",
        )

        parser.add_argument(
            "--email",
            default="",
            help="Email of the author",
        )

        parser.add_argument(
            "--directory",
            default=None,
            help="Directory to create the project in (defaults to project_name)",
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing files",
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: The parsed command-line arguments

        Returns:
            The exit code (0 for success, non-zero for failure)
        """
        # Get the project directory
        project_dir = args.directory or args.project_name
        project_dir = Path(project_dir)

        # Check if the directory exists
        if project_dir.exists() and not args.force:
            logger.error(
                f"Directory {project_dir} already exists. Use --force to overwrite."
            )
            return 1

        # Create the directory
        project_dir.mkdir(parents=True, exist_ok=True)

        # Get the package name (lowercase, with underscores)
        package_name = args.project_name.lower().replace("-", "_").replace(" ", "_")

        # Create the package directory
        package_dir = project_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Get the current year
        year = datetime.datetime.now().year

        # Create the template context
        context = {
            "project_name": args.project_name,
            "project_description": args.description,
            "package_name": package_name,
            "author_name": args.author,
            "author_email": args.email,
            "year": year,
        }

        # Create the project files
        for template_path, template_content in TEMPLATES.items():
            # Format the path with the context
            path = template_path.format(**context)

            # Get the full path
            full_path = project_dir / path

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Format the content with the context
            content = template_content.format(**context)

            # Write the file
            with open(full_path, "w") as f:
                f.write(content)

            logger.info(f"Created {full_path}")

        logger.info(f"Project {args.project_name} initialized in {project_dir}")
        logger.info("To get started, run:")
        logger.info(f"  cd {project_dir}")
        logger.info("  pip install -e .")

        return 0


@register_command
class RunCommand(Command):
    """Command to run a PepperPy application."""

    name = "run"
    description = "Run a PepperPy application"
    help = "Run a PepperPy application"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to
        """
        parser.add_argument(
            "app",
            help="Path to the application module or script",
        )

        parser.add_argument(
            "--config",
            help="Path to the configuration file",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode",
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: The parsed command-line arguments

        Returns:
            The exit code (0 for success, non-zero for failure)
        """
        # Get the application path
        app_path = args.app

        # Check if the path exists
        if not os.path.exists(app_path):
            logger.error(f"Application path {app_path} does not exist")
            return 1

        # If the path is a directory, look for app.py
        if os.path.isdir(app_path):
            app_path = os.path.join(app_path, "app.py")
            if not os.path.exists(app_path):
                logger.error(f"Application file {app_path} does not exist")
                return 1

        # If the path is a Python file, import it
        if app_path.endswith(".py"):
            # Get the directory containing the file
            app_dir = os.path.dirname(os.path.abspath(app_path))

            # Add the directory to the Python path
            sys.path.insert(0, app_dir)

            # Get the module name
            module_name = os.path.basename(app_path)[:-3]

            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Check if the module has a run function
                if hasattr(module, "run") and callable(module.run):
                    # Set up the environment
                    os.environ["PEPPERPY_DEBUG"] = "1" if args.debug else "0"

                    if args.config:
                        os.environ["PEPPERPY_CONFIG"] = os.path.abspath(args.config)

                    # Run the application
                    logger.info(f"Running application {module_name}")
                    module.run()

                    return 0
                else:
                    logger.error(f"Module {module_name} does not have a run function")
                    return 1
            except ImportError as e:
                logger.error(f"Failed to import module {module_name}: {str(e)}")
                return 1
            except Exception as e:
                logger.error(f"Error running application: {str(e)}")
                logger.debug("Exception details:", exc_info=True)
                return 1
        else:
            logger.error(f"Unsupported application file: {app_path}")
            return 1


@register_command
class VersionCommand(Command):
    """Command to show the PepperPy version."""

    name = "version"
    description = "Show the PepperPy version"
    help = "Show the PepperPy version"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to
        """
        pass

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: The parsed command-line arguments

        Returns:
            The exit code (0 for success, non-zero for failure)
        """
        # Import here to avoid circular imports
        from pepperpy import __version__

        print(f"PepperPy version: {__version__}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
