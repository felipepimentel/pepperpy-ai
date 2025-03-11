"""Commands for the PepperPy CLI.

This module provides the commands for the PepperPy CLI, including:
- init: Initialize a new PepperPy project
- run: Run a PepperPy application
"""

import argparse
import datetime
import importlib
import os
import sys
from pathlib import Path
from typing import Dict

from pepperpy.cli.core import Command, register_command
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Templates for project files
TEMPLATES: Dict[str, str] = {
    "README.md": """# {project_name}

A PepperPy project.

## Installation

```bash
pip install -e .
```

## Usage

```python
from {package_name} import app

app.run()
```
""",
    "setup.py": """from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    description="{project_description}",
    author="{author_name}",
    author_email="{author_email}",
    packages=find_packages(),
    install_requires=[
        "pepperpy",
    ],
    python_requires=">=3.8",
)
""",
    "{package_name}/__init__.py": """\"\"\"
{project_name}

{project_description}
\"\"\"

__version__ = "0.1.0"
""",
    "{package_name}/app.py": """\"\"\"
Application entry point.
\"\"\"

import pepperpy
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


def run():
    \"\"\"Run the application.\"\"\"
    logger.info("Hello from PepperPy!")
    logger.info(f"PepperPy version: {pepperpy.__version__}")
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
logs/
""",
    "LICENSE": """Copyright (c) {year} {author_name}

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
