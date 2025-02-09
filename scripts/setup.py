#!/usr/bin/env python3
"""Setup script for the Pepperpy project.

This script handles the initial setup and configuration of the Pepperpy project.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Define trusted commands and their allowed arguments
TRUSTED_COMMANDS: dict[str, Tuple[List[str], List[str]]] = {
    "pip": (
        ["python", "-m", "pip"],
        ["install", "--upgrade", "-r"],
    ),
    "pre-commit": (
        ["pre-commit"],
        ["install"],
    ),
    "poetry": (
        ["poetry"],
        ["install", "update", "add", "remove", "--dev", "--with", "--without"],
    ),
}


def validate_command(cmd: List[str]) -> bool:
    """Validate that a command is trusted and its arguments are allowed.

    Args:
        cmd: Command to validate as a list of arguments

    Returns:
        True if command is trusted and arguments are allowed
    """
    if not cmd:
        return False

    # Get command name and base command
    cmd_name = cmd[0] if cmd[0] != "python" else "pip"
    if cmd_name not in TRUSTED_COMMANDS:
        return False

    # Get trusted base command and allowed arguments
    base_cmd, allowed_args = TRUSTED_COMMANDS[cmd_name]

    # Check if command starts with trusted base command
    if not cmd[: len(base_cmd)] == base_cmd:
        return False

    # Check if all arguments are allowed
    args = cmd[len(base_cmd) :]
    return all(
        arg.startswith(tuple(allowed_args)) or os.path.exists(arg) for arg in args
    )


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command safely.

    Args:
        cmd: Command to run as a list of strings
        check: Whether to check return code

    Returns:
        CompletedProcess instance
    """
    if not validate_command(cmd):
        raise ValueError("Command not trusted")

    try:
        result = subprocess.run(  # noqa: S603 - Commands are validated through validate_command()
            cmd,
            check=check,
            capture_output=True,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        raise


def install_dependencies() -> None:
    """Install project dependencies."""
    print("Installing dependencies...")
    run_command(["poetry", "install"])


def install_pre_commit() -> None:
    """Install pre-commit hooks."""
    print("Installing pre-commit hooks...")
    run_command(["pre-commit", "install"])


def setup_environment() -> None:
    """Set up the development environment."""
    try:
        install_dependencies()
        install_pre_commit()
        print("Environment setup completed successfully!")
    except Exception as e:
        print(f"Environment setup failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    print("Setting up development environment...")

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Run setup steps
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Installing pre-commit hooks", install_pre_commit),
    ]

    success = True
    for step_name, step_func in steps:
        print(f"\n=== {step_name} ===")
        try:
            step_func()
            print(f"✅ {step_name} completed!")
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            success = False

    if success:
        print("\n✨ Development environment setup complete!")
    else:
        print("\n❌ Setup failed! Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
