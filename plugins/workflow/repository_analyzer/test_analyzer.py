"""Test script for repository analyzer workflow."""

import asyncio
import os

from plugins.workflow.repository_analyzer.simplified_adapter import (
    SimpleRepositoryAnalyzerAdapter,
)


async def test_repository_analysis() -> None:
    """Test repository analysis workflow."""
    # Create the adapter
    adapter = SimpleRepositoryAnalyzerAdapter()

    # Initialize the adapter
    await adapter.initialize()

    try:
        # Get current directory for analysis
        current_dir = os.getcwd()
        print(f"Analyzing repository at {current_dir}")

        # Analyze the repository structure
        result = await adapter.execute({
            "task": "analyze_structure",
            "input": {
                "repo_path": current_dir,
                "max_depth": 2,
                "include_patterns": ["*.py", "*.md"],
                "exclude_patterns": ["**/__pycache__/**"],
            },
        })

        # Print the result summary
        if result.get("status") == "success":
            print("\n✅ Analysis completed successfully!")

            # Print structure summary
            structure = result.get("structure", {})
            print(f"\n📁 Directory count: {structure.get('directory_count', 0)}")
            print(f"📄 File count: {structure.get('file_count', 0)}")

            # Print a few files
            files = structure.get("files", [])[:5]
            if files:
                print("\n📄 Sample files:")
                for file in files:
                    print(f"  - {file.get('path', 'Unknown')}")
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")

    finally:
        # Clean up adapter resources
        await adapter.cleanup()


async def test_code_quality_analysis() -> None:
    """Test code quality analysis workflow."""
    # Create the adapter
    adapter = SimpleRepositoryAnalyzerAdapter()

    # Initialize the adapter
    await adapter.initialize()

    try:
        # Get current directory for analysis
        current_dir = os.getcwd()
        print(f"Analyzing code quality at {current_dir}")

        # Analyze code quality
        result = await adapter.execute({
            "task": "analyze_code_quality",
            "input": {
                "repo_path": current_dir,
                "file_patterns": ["plugins/workflow/repository_analyzer/*.py"],
                "max_files": 2,
            },
        })

        # Print the result summary
        if result.get("status") == "success":
            print("\n✅ Quality analysis completed successfully!")

            # Print quality metrics
            metrics = result.get("file_analysis", {})
            print("\n📊 Quality metrics:")
            for file_path, metrics in list(metrics.items())[:3]:  # Show first 3 files
                print(f"  {file_path}:")
                for metric, value in metrics.items():
                    print(f"    - {metric}: {value}")
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")

    finally:
        # Clean up adapter resources
        await adapter.cleanup()


async def main() -> None:
    """Run the test workflow."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Repository Analyzer")
    parser.add_argument(
        "--task",
        type=str,
        choices=["structure", "quality", "all"],
        default="structure",
        help="The analysis task to run",
    )

    args = parser.parse_args()

    if args.task == "structure" or args.task == "all":
        print("\n🔍 TESTING REPOSITORY STRUCTURE ANALYSIS\n")
        await test_repository_analysis()

    if args.task == "quality" or args.task == "all":
        print("\n🔍 TESTING CODE QUALITY ANALYSIS\n")
        await test_code_quality_analysis()


if __name__ == "__main__":
    asyncio.run(main())
