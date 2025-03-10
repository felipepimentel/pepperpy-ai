"""Run command for the PepperPy CLI.

This module provides the run command for the PepperPy CLI, which runs
a PepperPy application.
"""

import argparse
import importlib
import os
import sys

from pepperpy.cli.core import Command, register_command
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


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
