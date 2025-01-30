#!/usr/bin/env python3
"""
@file: validate_structure.py
@purpose: Validate project structure against project_structure.yml
@component: Development Tools
@created: 2024-03-20
@task: TASK-000
@status: active
"""

from pathlib import Path
import sys
from typing import Dict, List, Optional, Set

import yaml


class StructureValidator:
    """Validates project structure against definition."""

    def __init__(self, project_root: Path):
        """Initialize validator."""
        self.project_root = project_root
        self.structure_file = project_root / "project_structure.yml"
        self.definition = self._load_definition()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _load_definition(self) -> Dict:
        """Load structure definition."""
        try:
            with open(self.structure_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading structure definition: {e}")
            sys.exit(1)

    def _validate_component(
        self, path: Path, definition: Dict, parent_path: str = ""
    ) -> None:
        """Validate a component against its definition."""
        full_path = parent_path + "/" + path.name if parent_path else path.name

        # Check if component exists
        if not path.exists():
            if definition.get("status") == "required":
                self.errors.append(f"Missing required component: {full_path}")
            elif definition.get("status") == "pending":
                task = definition.get("task", "Unknown")
                self.warnings.append(
                    f"Pending component not yet created: {full_path} (Task: {task})"
                )
            return

        # Check component type
        if path.is_dir():
            if "components" not in definition:
                self.errors.append(
                    f"Directory without components definition: {full_path}"
                )
                return

            # Check each subcomponent
            for name, subdef in definition["components"].items():
                subpath = path / name
                self._validate_component(subpath, subdef, full_path)

            # Check for unexpected files
            expected = set(definition["components"].keys())
            actual = {p.name for p in path.iterdir() if not p.name.startswith(".")}
            unexpected = actual - expected

            if unexpected:
                self.warnings.append(
                    f"Unexpected files in {full_path}: {', '.join(unexpected)}"
                )

    def validate(self) -> bool:
        """Validate entire project structure."""
        self.errors = []
        self.warnings = []

        # Validate version
        if "version" not in self.definition:
            self.errors.append("Missing version in structure definition")
            return False

        # Validate structure
        if "structure" not in self.definition:
            self.errors.append("Missing structure in definition")
            return False

        # Validate each top-level component
        for path_str, definition in self.definition["structure"].items():
            path = self.project_root / path_str.rstrip("/")
            self._validate_component(path, definition)

        # Print results
        if self.errors:
            print("\n❌ Structure validation failed!")
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Structure validation passed!")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        return len(self.errors) == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent
    validator = StructureValidator(project_root)

    if not validator.validate():
        sys.exit(1)


if __name__ == "__main__":
    main()
