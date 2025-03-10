"""Init command for the PepperPy CLI.

This module provides the init command for the PepperPy CLI, which initializes
a new PepperPy project.
"""

import argparse
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

# Run the app
app.run()
```
""",
    "pyproject.toml": """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "0.1.0"
description = "{project_description}"
readme = "README.md"
requires-python = ">=3.8"
license = {{file = "LICENSE"}}
authors = [
    {{name = "{author_name}", email = "{author_email}"}}
]
dependencies = [
    "pepperpy>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
    "mypy>=1.0.0",
]

[tool.setuptools]
packages = {{find = {{include = ["{package_name}"]}}}}

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
{project_name} - {project_description}
\"\"\"

__version__ = "0.1.0"
""",
    "{package_name}/app.py": """\"\"\"
Main application module.
\"\"\"

from pepperpy.core import get_logger

logger = get_logger(__name__)


def run() -> None:
    \"\"\"Run the application.\"\"\"
    logger.info("Running {project_name}...")
""",
    "{package_name}/config.py": """\"\"\"
Configuration module.
\"\"\"

from dataclasses import dataclass
from typing import Optional

from pepperpy.config import ConfigSection


@dataclass
class AppConfig(ConfigSection):
    \"\"\"Application configuration.\"\"\"
    
    # Add your configuration options here
    debug: bool = False
    api_key: Optional[str] = None
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
        import datetime

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
