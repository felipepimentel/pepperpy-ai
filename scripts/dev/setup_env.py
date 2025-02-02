#!/usr/bin/env python3
"""Development Environment Setup Script.

This script sets up the development environment for the project.
It handles:
- Creating virtual environment
- Installing dependencies
- Setting up pre-commit hooks
- Configuring development tools
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pepperpy.monitoring import logger


@dataclass
class SetupStep:
    """A step in the setup process."""

    name: str
    command: list[str]
    description: str
    optional: bool = False


class EnvSetup:
    """Handles development environment setup."""

    def __init__(self, workspace: Path):
        """Initialize the setup handler.

        Args:
            workspace: Root workspace directory
        """
        self.workspace = workspace
        self.venv_dir = workspace / ".venv"
        self.python = str(self.venv_dir / "bin" / "python")
        self.pip = str(self.venv_dir / "bin" / "pip")

    def get_setup_steps(self) -> list[SetupStep]:
        """Get the list of setup steps.

        Returns:
            List of setup steps to execute
        """
        return [
            SetupStep(
                name="venv",
                command=["python3", "-m", "venv", str(self.venv_dir)],
                description="Create virtual environment",
            ),
            SetupStep(
                name="pip-upgrade",
                command=[self.pip, "install", "--upgrade", "pip"],
                description="Upgrade pip",
            ),
            SetupStep(
                name="poetry",
                command=[self.pip, "install", "poetry"],
                description="Install poetry",
            ),
            SetupStep(
                name="dependencies",
                command=["poetry", "install"],
                description="Install project dependencies",
            ),
            SetupStep(
                name="pre-commit",
                command=[self.pip, "install", "pre-commit"],
                description="Install pre-commit",
            ),
            SetupStep(
                name="pre-commit-hooks",
                command=["pre-commit", "install"],
                description="Install pre-commit hooks",
            ),
            SetupStep(
                name="pytest",
                command=[self.pip, "install", "pytest", "pytest-cov"],
                description="Install test dependencies",
            ),
            SetupStep(
                name="mypy",
                command=[self.pip, "install", "mypy"],
                description="Install type checker",
                optional=True,
            ),
            SetupStep(
                name="black",
                command=[self.pip, "install", "black"],
                description="Install code formatter",
                optional=True,
            ),
            SetupStep(
                name="ruff",
                command=[self.pip, "install", "ruff"],
                description="Install linter",
                optional=True,
            ),
        ]

    def run_step(self, step: SetupStep) -> bool:
        """Run a setup step.

        Args:
            step: Setup step to run

        Returns:
            True if step succeeded, False otherwise
        """
        try:
            logger.info(
                f"Running setup step: {step.name}", description=step.description
            )

            result = subprocess.run(
                step.command,
                cwd=self.workspace,
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                if step.optional:
                    logger.warning(
                        f"Optional step failed: {step.name}", error=result.stderr
                    )
                    return True
                else:
                    logger.error(f"Step failed: {step.name}", error=result.stderr)
                    return False

            logger.info(f"Step completed: {step.name}")
            return True

        except Exception as e:
            if step.optional:
                logger.warning(f"Optional step failed: {step.name}", error=str(e))
                return True
            else:
                logger.error(f"Step failed: {step.name}", error=str(e))
                return False

    def setup(self, steps: list[str] | None = None) -> bool:
        """Run the setup process.

        Args:
            steps: Optional list of specific steps to run

        Returns:
            True if setup succeeded, False otherwise
        """
        all_steps = self.get_setup_steps()

        if steps:
            # Filter steps by name
            selected_steps = [step for step in all_steps if step.name in steps]
            if not selected_steps:
                logger.error(
                    "No valid steps selected",
                    available_steps=[s.name for s in all_steps],
                )
                return False
        else:
            selected_steps = all_steps

        for step in selected_steps:
            if not self.run_step(step):
                return False

        logger.info("Setup completed successfully")
        return True


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Setup development environment")
    parser.add_argument("--steps", nargs="*", help="Specific setup steps to run")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Workspace root directory",
    )
    args = parser.parse_args()

    setup = EnvSetup(args.workspace)
    success = setup.setup(args.steps)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
