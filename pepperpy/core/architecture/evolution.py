"""Architecture evolution management.

This module provides tools for managing architectural evolution.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pepperpy.core.architecture.validator import ArchitectureValidator


@dataclass
class EvolutionRecord:
    """Record of architectural evolution."""

    timestamp: str
    changes: list[str]
    validation_results: dict[str, Any]
    commit_hash: str | None = None
    author: str | None = None
    description: str | None = None


class EvolutionManager:
    """Manages architectural evolution."""

    def __init__(
        self,
        project_path: str | Path,
        rules_dir: str | Path,
        history_file: str | Path | None = None,
    ) -> None:
        """Initialize evolution manager.

        Args:
            project_path: Path to project root
            rules_dir: Directory containing rule files
            history_file: Optional path to history file
        """
        self.project_path = Path(project_path)
        self.validator = ArchitectureValidator(rules_dir)
        self.history_file = (
            Path(history_file)
            if history_file
            else self.project_path / ".architecture" / "evolution.json"
        )
        self.history: list[EvolutionRecord] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load evolution history."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                data = json.load(f)
                self.history = [EvolutionRecord(**record) for record in data]

    def _save_history(self) -> None:
        """Save evolution history."""
        # Create parent directory if it doesn't exist
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Save history
        with open(self.history_file, "w") as f:
            json.dump(
                [
                    {
                        "timestamp": record.timestamp,
                        "changes": record.changes,
                        "validation_results": record.validation_results,
                        "commit_hash": record.commit_hash,
                        "author": record.author,
                        "description": record.description,
                    }
                    for record in self.history
                ],
                f,
                indent=2,
            )

    def record_changes(
        self,
        changes: list[str],
        commit_hash: str | None = None,
        author: str | None = None,
        description: str | None = None,
    ) -> None:
        """Record architectural changes.

        Args:
            changes: List of changes made
            commit_hash: Optional commit hash
            author: Optional author name
            description: Optional change description
        """
        # Validate current state
        validation_results = self.validator.validate_project(self.project_path)

        # Create record
        record = EvolutionRecord(
            timestamp=datetime.now().isoformat(),
            changes=changes,
            validation_results=validation_results,
            commit_hash=commit_hash,
            author=author,
            description=description,
        )

        # Add to history and save
        self.history.append(record)
        self._save_history()

    def get_latest_validation(self) -> dict[str, Any]:
        """Get latest validation results.

        Returns:
            Latest validation results or empty dict if no history
        """
        if not self.history:
            return {}
        return self.history[-1].validation_results

    def get_validation_trend(self) -> list[tuple[str, float]]:
        """Get trend of validation success rate.

        Returns:
            List of (timestamp, success_rate) tuples
        """
        trend = []
        for record in self.history:
            success_rate = 0.0
            total_rules = 0

            for module_results in record.validation_results.values():
                valid_count = sum(1 for r in module_results if r.is_valid)
                total_rules += len(module_results)
                if total_rules > 0:
                    success_rate = valid_count / total_rules

            trend.append((record.timestamp, success_rate))

        return trend

    def generate_evolution_report(self) -> str:
        """Generate evolution report.

        Returns:
            Formatted report
        """
        report = ["# Architecture Evolution Report\n"]

        # Add summary
        report.append("\n## Summary\n")
        report.append(f"- Total changes recorded: {len(self.history)}\n")
        if self.history:
            first = self.history[0]
            last = self.history[-1]
            report.append(f"- First change: {first.timestamp}\n")
            report.append(f"- Latest change: {last.timestamp}\n")

            # Calculate success rate trend
            trend = self.get_validation_trend()
            if trend:
                initial_rate = trend[0][1] * 100
                final_rate = trend[-1][1] * 100
                report.append(
                    f"- Validation success rate: {initial_rate:.1f}% → {final_rate:.1f}%\n"
                )

        # Add recent changes
        report.append("\n## Recent Changes\n")
        for record in reversed(self.history[-5:]):
            report.append(f"\n### {record.timestamp}\n")
            if record.description:
                report.append(f"_{record.description}_\n\n")
            if record.author:
                report.append(f"**Author:** {record.author}\n")
            if record.commit_hash:
                report.append(f"**Commit:** {record.commit_hash}\n")
            report.append("\nChanges:\n")
            for change in record.changes:
                report.append(f"- {change}\n")

        # Add latest validation results
        report.append("\n## Latest Validation Results\n")
        if self.history:
            report.append(
                self.validator.generate_report(self.history[-1].validation_results)
            )
        else:
            report.append("No validation results available.\n")

        return "".join(report)


__all__ = ["EvolutionManager", "EvolutionRecord"]
