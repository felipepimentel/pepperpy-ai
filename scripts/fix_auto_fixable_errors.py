#!/usr/bin/env python3
"""
Script to fix auto-fixable lint errors in the codebase.
This script runs ruff with the --fix flag to automatically fix certain errors.
"""

import subprocess
from typing import List, Tuple


def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


def fix_auto_fixable_errors() -> None:
    """Fix auto-fixable lint errors."""
    # List of auto-fixable error codes
    auto_fixable_codes = ["I001", "F841", "B007", "B028"]

    # Run ruff with --fix flag for each auto-fixable error code
    for code in auto_fixable_codes:
        print(f"Fixing {code} errors...")
        command = ["ruff", "check", "pepperpy/", "--select", code, "--fix"]
        exit_code, stdout, stderr = run_command(command)

        if exit_code != 0:
            print(f"Warning: ruff exited with code {exit_code}")
            if stderr:
                print(f"Error: {stderr}")

        if stdout:
            print(stdout)

    # Run isort to fix import ordering
    print("Running isort to fix import ordering...")
    command = ["isort", "pepperpy/"]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        print(f"Warning: isort exited with code {exit_code}")
        if stderr:
            print(f"Error: {stderr}")

    if stdout:
        print(stdout)

    # Run black to fix formatting
    print("Running black to fix formatting...")
    command = ["black", "pepperpy/"]
    exit_code, stdout, stderr = run_command(command)

    if exit_code != 0:
        print(f"Warning: black exited with code {exit_code}")
        if stderr:
            print(f"Error: {stderr}")

    if stdout:
        print(stdout)


def main() -> None:
    """Main function."""
    print("Fixing auto-fixable lint errors...")
    fix_auto_fixable_errors()
    print("Done!")


if __name__ == "__main__":
    main()
