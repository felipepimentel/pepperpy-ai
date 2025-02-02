#!/usr/bin/env python3
"""Setup script for the Pepperpy project.

This script handles the initial setup and configuration of the Pepperpy project.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str) -> bool:
    """Run a shell command."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e}")
        return False


def install_dependencies() -> bool:
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")

    # Core dependencies
    core_deps = [
        "pydantic>=2.6.1",
        "pyyaml>=6.0.1",
        "loguru>=0.7.2",
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "mypy>=1.8.0",
        "black>=24.1.1",
        "isort>=5.13.2",
        "pylint>=3.0.3",
        "pre-commit>=3.6.0",
    ]

    # Create requirements.txt
    requirements_file = Path("requirements.txt")
    with open(requirements_file, "w") as f:
        f.write("\n".join(core_deps))

    # Install dependencies
    return run_command("pip install -r requirements.txt")


def setup_git_hooks() -> bool:
    """Setup git hooks using pre-commit."""
    print("\nSetting up git hooks...")

    # Create pre-commit config
    precommit_config = """repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort

-   repo: local
    hooks:
    -   id: validate-structure
        name: validate-structure
        entry: python scripts/validate_structure.py
        language: python
        pass_filenames: false
        always_run: true

    -   id: validate-headers
        name: validate-headers
        entry: python scripts/validate_headers.py
        language: python
        pass_filenames: false
        always_run: true

    -   id: check-duplicates
        name: check-duplicates
        entry: python scripts/check_duplicates.py
        language: python
        pass_filenames: false
        always_run: true"""

    with open(".pre-commit-config.yaml", "w") as f:
        f.write(precommit_config)

    # Install pre-commit hooks
    return run_command("pre-commit install")


def create_env_template() -> bool:
    """Create .env.example template."""
    print("\nCreating .env template...")

    env_template = """# Environment Configuration
PEPPERPY_ENV=development
PEPPERPY_DEBUG=true

# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here

# Logging Configuration
PEPPERPY_LOG_LEVEL=DEBUG
PEPPERPY_LOG_FORMAT="{time} | {level} | {message}"

# Memory Configuration
PEPPERPY_MEMORY_STORE=faiss
PEPPERPY_MEMORY_EMBEDDING_SIZE=512

# Provider Configuration
PEPPERPY_ENABLED_PROVIDERS=["openai", "local"]
PEPPERPY_DEFAULT_MODEL=gpt-4"""

    with open(".env.example", "w") as f:
        f.write(env_template)

    return True


def setup_project() -> None:
    """Set up the Pepperpy project.

    Creates necessary directories and configuration files.
    """
    # TODO: Implement project setup
    pass


def main() -> None:
    """Main entry point."""
    print("Setting up development environment...")

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Run setup steps
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up git hooks", setup_git_hooks),
        ("Creating .env template", create_env_template),
    ]

    success = True
    for step_name, step_func in steps:
        print(f"\n=== {step_name} ===")
        if not step_func():
            print(f"❌ {step_name} failed!")
            success = False
        else:
            print(f"✅ {step_name} completed!")

    if success:
        print("\n✨ Development environment setup complete!")
    else:
        print("\n❌ Setup failed! Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
