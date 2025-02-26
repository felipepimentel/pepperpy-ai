"""Architecture validation functionality.

This module provides tools for validating architectural patterns and rules.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ArchitectureRule:
    """Rule for architectural validation."""

    name: str
    description: str
    patterns: list[str]
    forbidden_patterns: list[str] = field(default_factory=list)
    required_files: list[str] = field(default_factory=list)
    allowed_imports: list[str] = field(default_factory=list)
    forbidden_imports: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of architectural validation."""

    rule: ArchitectureRule
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ArchitectureValidator:
    """Validates architectural patterns and rules."""

    def __init__(self, rules_dir: str | Path) -> None:
        """Initialize validator.

        Args:
            rules_dir: Directory containing rule files
        """
        self.rules_dir = Path(rules_dir)
        self.rules: dict[str, ArchitectureRule] = {}
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from rule files."""
        for rule_file in self.rules_dir.glob("*.yml"):
            with open(rule_file) as f:
                rule_data = yaml.safe_load(f)
                rule = ArchitectureRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    patterns=rule_data["patterns"],
                    forbidden_patterns=rule_data.get("forbidden_patterns", []),
                    required_files=rule_data.get("required_files", []),
                    allowed_imports=rule_data.get("allowed_imports", []),
                    forbidden_imports=rule_data.get("forbidden_imports", []),
                )
                self.rules[rule.name] = rule

    def validate_module(self, module_path: str | Path) -> list[ValidationResult]:
        """Validate a module against architectural rules.

        Args:
            module_path: Path to module to validate

        Returns:
            List of validation results
        """
        results = []
        module_path = Path(module_path)

        for rule in self.rules.values():
            result = ValidationResult(rule=rule, is_valid=True)

            # Check patterns
            for pattern in rule.patterns:
                if not any(module_path.glob(pattern)):
                    result.is_valid = False
                    result.errors.append(f"Missing required pattern: {pattern}")

            # Check forbidden patterns
            for pattern in rule.forbidden_patterns:
                if any(module_path.glob(pattern)):
                    result.is_valid = False
                    result.errors.append(f"Found forbidden pattern: {pattern}")

            # Check required files
            for file_pattern in rule.required_files:
                if not any(module_path.glob(file_pattern)):
                    result.is_valid = False
                    result.errors.append(f"Missing required file: {file_pattern}")

            # Check imports
            for py_file in module_path.rglob("*.py"):
                with open(py_file) as f:
                    content = f.read()
                    imports = self._extract_imports(content)

                    # Check allowed imports
                    if rule.allowed_imports:
                        for imp in imports:
                            if not any(
                                re.match(pattern, imp)
                                for pattern in rule.allowed_imports
                            ):
                                result.is_valid = False
                                result.errors.append(
                                    f"Import {imp} in {py_file} not allowed"
                                )

                    # Check forbidden imports
                    for imp in imports:
                        if any(
                            re.match(pattern, imp) for pattern in rule.forbidden_imports
                        ):
                            result.is_valid = False
                            result.errors.append(
                                f"Import {imp} in {py_file} is forbidden"
                            )

            results.append(result)

        return results

    def _extract_imports(self, content: str) -> set[str]:
        """Extract imports from Python content.

        Args:
            content: Python file content

        Returns:
            Set of import statements
        """
        imports = set()
        import_pattern = r"^\s*(import|from)\s+([^\s]+)"

        for line in content.split("\n"):
            match = re.match(import_pattern, line)
            if match:
                imports.add(match.group(2).split(" ")[0])

        return imports

    def validate_project(self, project_path: str | Path) -> dict[str, Any]:
        """Validate entire project.

        Args:
            project_path: Path to project root

        Returns:
            Validation results by module
        """
        project_path = Path(project_path)
        results = {}

        for module_dir in project_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("."):
                results[module_dir.name] = self.validate_module(module_dir)

        return results

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate validation report.

        Args:
            results: Validation results

        Returns:
            Formatted report
        """
        report = ["# Architecture Validation Report\n"]

        for module_name, module_results in results.items():
            report.append(f"\n## {module_name}\n")
            valid_count = sum(1 for r in module_results if r.is_valid)
            total_count = len(module_results)
            report.append(
                f"- {valid_count}/{total_count} rules passed "
                f"({valid_count / total_count * 100:.1f}%)\n"
            )

            for result in module_results:
                status = "✅" if result.is_valid else "❌"
                report.append(f"\n### {status} {result.rule.name}\n")
                report.append(f"_{result.rule.description}_\n")

                if not result.is_valid:
                    report.append("\nErrors:\n")
                    for error in result.errors:
                        report.append(f"- {error}\n")

                if result.warnings:
                    report.append("\nWarnings:\n")
                    for warning in result.warnings:
                        report.append(f"- {warning}\n")

        return "".join(report)


__all__ = ["ArchitectureRule", "ArchitectureValidator", "ValidationResult"]
