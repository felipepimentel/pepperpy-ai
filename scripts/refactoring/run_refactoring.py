#!/usr/bin/env python3
"""
Run Refactoring Script

This script coordinates the execution of the PepperPy refactoring process.
It allows running specific phases or all phases in sequence, and generates
a final report of the refactoring process.

Usage:
    python run_refactoring.py --all
    python run_refactoring.py --consolidate
    python run_refactoring.py --reorganize
"""

import argparse
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("refactoring.log"), logging.StreamHandler()],
)
logger = logging.getLogger("run_refactoring")


def import_module_from_file(file_path: Path) -> Optional[Any]:
    """
    Import a module from a file path.

    Args:
        file_path: Path to the Python file to import

    Returns:
        The imported module or None if import failed
    """
    try:
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error(
                f"Failed to create spec for module {module_name} from {file_path}"
            )
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error importing module from {file_path}: {str(e)}")
        return None


def run_consolidation_phase(project_root: Path) -> Optional[str]:
    """
    Run the consolidation phase of the refactoring process.

    Args:
        project_root: Root of the project

    Returns:
        Path to the generated report or None if phase failed
    """
    logger.info("Running consolidation phase")

    # Import the consolidate_duplicates module
    consolidate_file = Path(__file__).parent / "consolidate_duplicates.py"
    consolidate_module = import_module_from_file(consolidate_file)

    if consolidate_module is None:
        logger.error("Failed to import consolidate_duplicates module")
        return None

    # Run the consolidation process
    try:
        report_path = consolidate_module.run_consolidation(project_root)
        logger.info(
            f"Consolidation phase completed successfully. Report at {report_path}"
        )
        return report_path
    except Exception as e:
        logger.error(f"Error running consolidation phase: {str(e)}")
        return None


def run_reorganization_phase(project_root: Path) -> Optional[str]:
    """
    Run the reorganization phase of the refactoring process.

    Args:
        project_root: Root of the project

    Returns:
        Path to the generated report or None if phase failed
    """
    logger.info("Running reorganization phase")

    # Import the reorganize_structure module
    reorganize_file = Path(__file__).parent / "reorganize_structure.py"
    reorganize_module = import_module_from_file(reorganize_file)

    if reorganize_module is None:
        logger.error("Failed to import reorganize_structure module")
        return None

    # Run the reorganization process
    try:
        report_path = reorganize_module.run_reorganization(project_root)
        logger.info(
            f"Reorganization phase completed successfully. Report at {report_path}"
        )
        return report_path
    except Exception as e:
        logger.error(f"Error running reorganization phase: {str(e)}")
        return None


def generate_final_report(project_root: Path, phase_reports: Dict[str, str]) -> str:
    """
    Generate a final report of the refactoring process.

    Args:
        project_root: Root of the project
        phase_reports: Dictionary mapping phase names to report paths

    Returns:
        Path to the generated final report
    """
    logger.info("Generating final refactoring report")

    report_content = "# PepperPy Refactoring Final Report\n\n"

    # Add summary of phases executed
    report_content += "## Phases Executed\n\n"
    for phase, report_path in phase_reports.items():
        report_content += f"- {phase}: Completed successfully\n"

    # Add links to individual phase reports
    report_content += "\n## Phase Reports\n\n"
    for phase, report_path in phase_reports.items():
        report_content += f"- [{phase} Report]({os.path.basename(report_path)})\n"

    # Add next steps
    report_content += "\n## Next Steps\n\n"
    report_content += "1. Review the changes made during refactoring\n"
    report_content += "2. Update documentation to reflect the new structure\n"
    report_content += "3. Update tests to ensure they work with the new structure\n"
    report_content += "4. Implement a plan for gradual removal of compatibility stubs\n"

    # Write the report to a file
    report_path = project_root / "refactoring_final_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)

    logger.info(f"Final refactoring report generated at {report_path}")

    return str(report_path)


def main():
    """
    Main function to run the refactoring process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run PepperPy refactoring process")
    parser.add_argument("--all", action="store_true", help="Run all refactoring phases")
    parser.add_argument(
        "--consolidate", action="store_true", help="Run consolidation phase"
    )
    parser.add_argument(
        "--reorganize", action="store_true", help="Run reorganization phase"
    )
    args = parser.parse_args()

    # If no arguments provided, show help
    if not (args.all or args.consolidate or args.reorganize):
        parser.print_help()
        return

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Track phase reports
    phase_reports = {}

    # Run consolidation phase if requested
    if args.all or args.consolidate:
        consolidation_report = run_consolidation_phase(project_root)
        if consolidation_report:
            phase_reports["Consolidation"] = consolidation_report

    # Run reorganization phase if requested
    if args.all or args.reorganize:
        reorganization_report = run_reorganization_phase(project_root)
        if reorganization_report:
            phase_reports["Reorganization"] = reorganization_report

    # Generate final report if any phases were executed
    if phase_reports:
        final_report = generate_final_report(project_root, phase_reports)
        logger.info(f"Refactoring process completed. Final report at {final_report}")
    else:
        logger.warning("No refactoring phases were executed successfully")


if __name__ == "__main__":
    main()
