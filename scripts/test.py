#!/usr/bin/env python3
"""
@file: test.py
@purpose: Run tests with coverage and validation
@component: Development Tools
@created: 2024-03-20
@task: TASK-000
@status: active
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Optional


def run_command(cmd: str) -> bool:
    """Run a shell command."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def run_tests(
    paths: Optional[List[str]] = None,
    coverage: bool = True,
    verbose: bool = False,
    fail_under: int = 80,
) -> bool:
    """Run pytest with options."""
    cmd = ["pytest"]

    # Add paths or use default
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("tests/")

    # Add options
    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(
            [
                "--cov=pepperpy",
                "--cov-report=term-missing",
                "--cov-report=html",
                f"--cov-fail-under={fail_under}",
            ]
        )

    # Run tests
    return run_command(" ".join(cmd))


def run_type_checks() -> bool:
    """Run mypy type checking."""
    return run_command("mypy pepperpy/ tests/")


def run_linting() -> bool:
    """Run pylint."""
    return run_command("pylint pepperpy/ tests/")


def run_formatting() -> bool:
    """Run black and isort."""
    return all([run_command("black ."), run_command("isort .")])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run tests and validation")

    parser.add_argument("paths", nargs="*", help="Paths to test (default: tests/)")

    parser.add_argument(
        "--no-coverage", action="store_true", help="Disable coverage reporting"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--fail-under",
        type=int,
        default=80,
        help="Fail if coverage is under this percentage",
    )

    parser.add_argument(
        "--no-type-check", action="store_true", help="Skip type checking"
    )

    parser.add_argument("--no-lint", action="store_true", help="Skip linting")

    parser.add_argument("--no-format", action="store_true", help="Skip formatting")

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    success = True
    steps = []

    # Add selected steps
    if not args.no_format:
        steps.append(("Formatting code", run_formatting))

    if not args.no_type_check:
        steps.append(("Type checking", run_type_checks))

    if not args.no_lint:
        steps.append(("Linting", run_linting))

    steps.append(
        (
            "Running tests",
            lambda: run_tests(
                paths=args.paths,
                coverage=not args.no_coverage,
                verbose=args.verbose,
                fail_under=args.fail_under,
            ),
        )
    )

    # Run steps
    for step_name, step_func in steps:
        print(f"\n=== {step_name} ===")
        if not step_func():
            print(f"❌ {step_name} failed!")
            success = False
        else:
            print(f"✅ {step_name} completed!")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
