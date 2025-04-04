#!/usr/bin/env python3
"""Repository analysis example with PepperPy.

This example demonstrates PepperPy's modern declarative API for effortless
repository analysis - inspired by frameworks like AutoGen and CrewAI.
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy

# Define output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "repos"


async def main():
    """Analyze a repository with PepperPy's declarative API."""
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    # Setup analysis pipeline declaratively
    pepper = (
        PepperPy()
        .configure(
            output_dir=OUTPUT_DIR,
            log_level="INFO",
            log_to_console=True,
            auto_save_results=True,
        )
        .repo(repo_url)
    )

    # Define analyses - no execution yet, just configuration
    analyses = [
        # Basic analysis without enhancers
        pepper.analysis("basic")
        .prompt("Summarize this repository's purpose and structure")
        .output("basic_analysis.txt"),
        # Security focused analysis
        pepper.analysis("security")
        .prompt("Identify security concerns in this codebase")
        .enhance.security(compliance=["OWASP Top 10"])
        .output("security_analysis.txt"),
        # Architecture analysis with multiple enhancers
        pepper.analysis("architecture")
        .prompt("How can this codebase be improved architecturally?")
        .enhance.deep_context(depth=3)
        .enhance.best_practices(framework="Python")
        .enhance.performance(hotspots=True)
        .output("architecture_analysis.txt"),
        # Custom domain analysis with HCI focus
        pepper.analysis("usability")
        .prompt("How can the UI/UX be improved for better user experience?")
        .enhance.domain("human-computer-interaction")
        .output("usability_analysis.txt"),
    ]

    # Execute all analyses in a single call - can be run concurrently
    await pepper.run_analyses(analyses)

    # Print results
    print(f"\nAnalyses completed! All results saved to {OUTPUT_DIR}")
    for analysis in analyses:
        print(f"- {analysis.name}: {analysis.result[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
