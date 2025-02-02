"""Context validation utilities.

This module provides tools for validating context files and structures.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml


class ContextValidator:
    """Validator for context files and structures.

    This class provides functionality to validate context files and structures
    according to project requirements.
    """

    def __init__(self, docs_root: str = "docs") -> None:
        """Initialize the validator.

        Args:
            docs_root: Root directory for documentation files.
        """
        self.docs_path = Path(docs_root)
        self.requirements: dict[str, Sequence[str]] = {
            "context": ["overview", "goals", "constraints"],
            "architecture": ["components", "interfaces", "deployment"],
            "development": ["setup", "workflow", "guidelines"],
        }

    def validate_structure(self) -> dict[str, dict[str, str | list[dict[str, str]]]]:
        """Validate the context directory structure.

        Returns:
            A report containing validation results for each section.
        """
        report: dict[str, dict[str, str | list[dict[str, str]]]] = {}
        for section, components in self.requirements.items():
            section_path = self.docs_path / section
            if not section_path.exists():
                report[section] = {"status": "missing", "components": []}
                continue

            component_status: list[dict[str, str]] = []
            for component in components:
                component_path = section_path / f"{component}.md"
                status = "present" if component_path.exists() else "missing"
                component_status.append({"name": component, "status": status})

            report[section] = {"status": "present", "components": component_status}

        return report

    def check_file_sizes(self) -> list[dict[str, Any]]:
        """Check file sizes for potential issues.

        Returns:
            A list of files that exceed size thresholds.
        """
        oversized = []
        for md_file in self.docs_path.glob("**/*.md"):
            size = md_file.stat().st_size
            if size > 50000:  # 50KB threshold
                oversized.append({"file": str(md_file), "size": size})
        return oversized


if __name__ == "__main__":
    validator = ContextValidator()
    structure_report = validator.validate_structure()
    size_report = validator.check_file_sizes()

    print("Validation Report:")
    print(
        yaml.dump(
            {"structure_issues": structure_report, "oversized_files": size_report}
        )
    )


def validate_context(context_path: str) -> bool:
    """Validate a context file.

    Args:
        context_path: Path to the context file.

    Returns:
        True if validation succeeds, False otherwise.
    """
    # TODO: Implement context validation
    return True
