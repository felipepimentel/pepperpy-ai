#!/usr/bin/env python3
"""
Script to execute the provider consolidation plan.

This script:
1. Executes the consolidation of providers
2. Standardizes provider implementations
3. Cleans up redundant modules
4. Generates a progress report
"""

import datetime
import subprocess
import sys
from pathlib import Path

# Define paths
REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
REPORT_FILE = REPO_ROOT / "provider_consolidation_progress_report.md"

# Define scripts to execute
CONSOLIDATE_SCRIPT = SCRIPTS_DIR / "consolidate_providers.py"
STANDARDIZE_SCRIPT = SCRIPTS_DIR / "standardize_providers.py"
CLEANUP_SCRIPT = SCRIPTS_DIR / "cleanup_redundant_modules.py"


def run_script(script_path, description):
    """Run a script and return its output."""
    print(f"\n{'=' * 80}")
    print(f"Executing: {description}")
    print(f"{'=' * 80}\n")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        print(e.stdout)
        print(e.stderr)
        return False, e.stdout + "\n" + e.stderr


def generate_report(results):
    """Generate a progress report."""
    with open(REPORT_FILE, "w") as f:
        f.write("# Provider Consolidation Progress Report\n\n")
        f.write(
            f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        for phase, (success, output) in results.items():
            status = "✅ Completed" if success else "❌ Failed"
            f.write(f"## {phase}: {status}\n\n")
            f.write("```\n")
            f.write(output)
            f.write("\n```\n\n")

        # Add summary
        success_count = sum(1 for success, _ in results.values() if success)
        total_count = len(results)
        f.write("## Summary\n\n")
        f.write(f"- Total phases: {total_count}\n")
        f.write(f"- Completed phases: {success_count}\n")
        f.write(f"- Failed phases: {total_count - success_count}\n")

        if success_count == total_count:
            f.write("\n🎉 **All phases completed successfully!** 🎉\n")
        else:
            f.write(
                "\n⚠️ **Some phases failed. Please check the logs for details.** ⚠️\n"
            )

    print(f"\nProgress report generated: {REPORT_FILE}")


def confirm_execution(phase):
    """Ask for confirmation before executing a phase."""
    while True:
        response = input(f"\nExecute {phase}? (y/n): ").lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")


def main():
    """Main function to execute the provider consolidation plan."""
    print("Starting provider consolidation plan execution...")

    results = {}

    # Phase 1: Consolidate Providers
    if confirm_execution("Phase 1: Consolidate Providers"):
        results["Phase 1: Consolidate Providers"] = run_script(
            CONSOLIDATE_SCRIPT, "Consolidating providers"
        )
    else:
        print("Skipping Phase 1: Consolidate Providers")

    # Phase 2: Standardize Providers
    if confirm_execution("Phase 2: Standardize Providers"):
        results["Phase 2: Standardize Providers"] = run_script(
            STANDARDIZE_SCRIPT, "Standardizing providers"
        )
    else:
        print("Skipping Phase 2: Standardize Providers")

    # Phase 3: Clean Up Redundant Modules
    if confirm_execution("Phase 3: Clean Up Redundant Modules"):
        results["Phase 3: Clean Up Redundant Modules"] = run_script(
            CLEANUP_SCRIPT, "Cleaning up redundant modules"
        )
    else:
        print("Skipping Phase 3: Clean Up Redundant Modules")

    # Generate progress report
    if results:
        generate_report(results)

    print("\nProvider consolidation plan execution completed!")


if __name__ == "__main__":
    main()
