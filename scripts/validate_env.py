#!/usr/bin/env python
"""
Environment Variable Validation Script for PepperPy.

This script validates environment variables against the PepperPy naming convention 
and provides suggestions for fixing non-compliant variables.

Usage:
    python scripts/validate_env.py [--env-file .env]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List


class ValidationError:
    """Represents an environment variable validation error."""

    def __init__(self, var_name: str, message: str, suggestion: str | None = None):
        self.var_name = var_name
        self.message = message
        self.suggestion = suggestion


class EnvValidator:
    """Validates environment variables against PepperPy naming conventions."""

    # Valid domain prefixes
    VALID_DOMAINS = {
        "APP",
        "LLM",
        "RAG",
        "NEWS",
        "TTS",
        "IMAGE",
        "SEARCH",
        "MEMORY",
        "AGENT",
        "SECURITY",
        "DATABASE",
        "LOG",
        "FEATURE",
        "CORS",
        "API",
        "DEV",
        "PROJECT",
    }

    # Valid provider names
    VALID_PROVIDERS = {
        "OPENAI",
        "OPENROUTER",
        "ANTHROPIC",
        "GOOGLE",
        "ELEVENLABS",
        "STABILITY",
        "NEWSAPI",
        "NEWSDATA",
        "FINLIGHT",
        "SERPER",
    }

    # Pattern for valid environment variable names
    ENV_VAR_PATTERN = re.compile(r"^PEPPERPY_([A-Z]+)__([A-Z_]+)$")

    def __init__(self, env_file: str = None):
        """Initialize the validator with the environment file path."""
        self.env_file = env_file
        self.env_vars = self._load_env_vars()

    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from file or os.environ."""
        if not self.env_file:
            return dict(os.environ)

        env_path = Path(self.env_file)
        if not env_path.exists():
            print(f"Error: Environment file {self.env_file} not found.")
            sys.exit(1)

        env_vars = {}
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars

    def validate(self) -> List[ValidationError]:
        """Validate all environment variables and return errors."""
        errors = []
        pepperpy_vars = {
            k: v for k, v in self.env_vars.items() if k.startswith("PEPPERPY_")
        }

        for var_name in pepperpy_vars:
            # Skip Python environment variables
            if var_name in {"PYTHONHOME", "PYTHONPATH"}:
                continue

            # Check pattern
            match = self.ENV_VAR_PATTERN.match(var_name)
            if not match:
                suggestion = self._suggest_name(var_name)
                errors.append(
                    ValidationError(
                        var_name,
                        "Does not follow the PEPPERPY_DOMAIN__SETTING pattern",
                        suggestion,
                    )
                )
                continue

            # Check domain
            domain = match.group(1)
            if domain not in self.VALID_DOMAINS:
                errors.append(
                    ValidationError(
                        var_name,
                        f"Invalid domain: {domain}",
                        f"Use one of: {', '.join(sorted(self.VALID_DOMAINS))}",
                    )
                )

            # Check if provider is valid when present
            rest = match.group(2)
            for provider in self.VALID_PROVIDERS:
                if rest.startswith(f"{provider}_"):
                    break
            else:
                # It's okay if no provider is used
                pass

        return errors

    def _suggest_name(self, var_name: str) -> str:
        """Suggest a compliant name for the given variable."""
        if not var_name.startswith("PEPPERPY_"):
            return f"PEPPERPY_DOMAIN__{var_name}"

        # Handle single underscore case
        parts = var_name[9:].split("_", 1)
        if len(parts) >= 2:
            domain = parts[0]
            rest = parts[1]
            return f"PEPPERPY_{domain}__{rest}"

        return f"PEPPERPY_DOMAIN__{var_name[9:]}"

    def check_missing_required(self) -> List[ValidationError]:
        """Check for missing required environment variables."""
        # Define required variables by domain
        required_vars = [
            "PEPPERPY_APP__NAME",
            "PEPPERPY_APP__VERSION",
        ]

        errors = []
        for var in required_vars:
            if var not in self.env_vars or not self.env_vars[var]:
                errors.append(
                    ValidationError(
                        var,
                        "Required environment variable is missing or empty",
                        f"Set {var} to an appropriate value",
                    )
                )

        return errors

    def find_deprecated(self) -> List[ValidationError]:
        """Find deprecated environment variables."""
        # Define deprecated variables and their replacements
        deprecated_vars = {
            "OPENAI_API_KEY": "PEPPERPY_LLM__OPENAI_API_KEY",
            "OPENROUTER_API_KEY": "PEPPERPY_LLM__OPENROUTER_API_KEY",
            "NEWS_API_KEY": "PEPPERPY_NEWS__NEWSAPI_API_KEY",
            "PEPPERPY_TTS_KEY": "PEPPERPY_TTS__GOOGLE_API_KEY",
            "STABILITY_API_KEY": "PEPPERPY_IMAGE__STABILITY_API_KEY",
            "SERPER_API_KEY": "PEPPERPY_SEARCH__SERPER_API_KEY",
        }

        errors = []
        for old_var, new_var in deprecated_vars.items():
            if old_var in self.env_vars:
                errors.append(
                    ValidationError(
                        old_var,
                        "Deprecated environment variable",
                        f"Replace with {new_var}",
                    )
                )

        return errors

    def print_report(self) -> int:
        """Print validation report and return error count."""
        format_errors = self.validate()
        missing_errors = self.check_missing_required()
        deprecated_errors = self.find_deprecated()

        all_errors = format_errors + missing_errors + deprecated_errors

        if not all_errors:
            print(
                "✅ All environment variables comply with PepperPy naming conventions."
            )
            return 0

        print(f"❌ Found {len(all_errors)} issues with environment variables:")

        # Format issues
        if format_errors:
            print("\n📋 Format Issues:")
            for error in format_errors:
                print(f"  - {error.var_name}: {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")

        # Missing required variables
        if missing_errors:
            print("\n🔍 Missing Required Variables:")
            for error in missing_errors:
                print(f"  - {error.var_name}: {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")

        # Deprecated variables
        if deprecated_errors:
            print("\n⚠️ Deprecated Variables:")
            for error in deprecated_errors:
                print(f"  - {error.var_name}: {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")

        return len(all_errors)


def main():
    """Run the environment variable validator."""
    parser = argparse.ArgumentParser(
        description="Validate PepperPy environment variables"
    )
    parser.add_argument(
        "--env-file", default=".env", help="Path to the .env file (default: .env)"
    )

    args = parser.parse_args()
    validator = EnvValidator(args.env_file)
    error_count = validator.print_report()

    if error_count > 0:
        print(
            "\nSee .cursor/rules/003-environment-variables.mdc for naming conventions"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
