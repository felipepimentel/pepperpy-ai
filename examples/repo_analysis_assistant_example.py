"""Repository Analysis Assistant Example.

This example demonstrates a comprehensive code repository analysis assistant that:
1. Analyzes repository structure and organization
2. Evaluates code quality and maintainability
3. Identifies issues and recommends improvements
4. Generates documentation and diagrams
5. Performs security vulnerability scanning
6. Provides refactoring suggestions
7. Analyzes test coverage and quality
8. Allows interaction with the repository through natural language
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from pepperpy.tools.repository import RepositoryAnalyzer
from pepperpy.tools.repository.providers import GitHubProvider


async def analyze_repository(repo_identifier):
    """Analyze a repository and generate a report."""
    # Initialize GitHub provider (token is automatically loaded from environment)
    github = GitHubProvider()
    
    # Create repository analyzer with GitHub provider
    # Output directory is automatically created by the library
    analyzer = RepositoryAnalyzer(
        provider=github,
        output_dir="examples/output/repo_analysis"
    )
    
    print(f"\nAnalyzing GitHub repository: {repo_identifier}")
    
    # Run analysis pipeline
    report = await analyzer.analyze(repo_identifier)
    
    # Save the analysis report
    report_path = analyzer.save_report(report)
    
    return report, report_path


async def explain_architecture(report):
    """Generate an architecture explanation based on the analysis report."""
    # In a real implementation, this would use an LLM
    # For this example, we'll create a hardcoded explanation

    # Create a detailed explanation based on the report data
    explanation = [
        f"# Architecture Summary for {report.repository_name}",
        "",
        "## Language Distribution",
    ]
    
    # Add language distribution
    for lang, percentage in report.structure.languages.items():
        explanation.append(f"- {lang}: {percentage:.1f}%")
    
    # Add structure information
    explanation.append("")
    explanation.append("## Repository Structure")
    explanation.append(f"- Total files: {report.structure.files_count}")
    
    for dir_name, dir_info in report.structure.directories.items():
        explanation.append(f"- {dir_name}/: {dir_info['count']} files ({dir_info['type']})")
    
    # Add entry points
    if report.structure.entry_points:
        explanation.append("")
        explanation.append("## Entry Points")
        for entry in report.structure.entry_points:
            explanation.append(f"- {entry}")
    
    # Add code quality assessment
    explanation.append("")
    explanation.append("## Code Quality Assessment")
    explanation.append(f"- Maintainability: {report.code_quality.maintainability_index:.1f}/100")
    explanation.append(f"- Cyclomatic Complexity: {report.code_quality.cyclomatic_complexity:.1f}")
    explanation.append(f"- Code Duplication: {report.code_quality.code_duplication:.1f}%")
    explanation.append(f"- Test Coverage: {report.code_quality.test_coverage:.1f}%")
    explanation.append(f"- Documentation Coverage: {report.code_quality.documentation_coverage:.1f}%")
    
    # Add architectural recommendations
    explanation.append("")
    explanation.append("## Architectural Recommendations")
    for rec in report.recommendations:
        explanation.append(f"- {rec}")
    
    # Join into a single string
    return "\n".join(explanation)


async def main():
    """Run the repository analysis assistant example."""
    # Repository to analyze
    repo_identifier = "wonderwhy-er/ClaudeDesktopCommander"
    
    try:
        # Analyze repository
        report, report_path = await analyze_repository(repo_identifier)
        
        # Display summary information
        print(f"\nRepository Analysis Summary:")
        print(f"Repository: {report.repository_name} ({report.repository_url})")
        print(f"Files: {report.structure.files_count}")
        print(f"Languages: {', '.join(f'{lang} ({pct:.1f}%)' for lang, pct in report.structure.languages.items())}")
        print(f"Code Quality:")
        print(f"  - Maintainability: {report.code_quality.maintainability_index:.1f}/100")
        print(f"  - Test Coverage: {report.code_quality.test_coverage:.1f}%")
        print(f"  - Doc Coverage: {report.code_quality.documentation_coverage:.1f}%")
        
        # Display issues summary
        total_issues = sum(len(issues) for issues in report.code_quality.issues.values())
        print(f"Issues Found: {total_issues}")
        for severity, issues in report.code_quality.issues.items():
            if issues:
                print(f"  - {severity.capitalize()}: {len(issues)}")
        
        # Display top recommendations
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\nFull report saved to: {report_path}")
        
        # If the user wants an architecture explanation
        if "--explain-architecture" in sys.argv or "-e" in sys.argv:
            explanation = await explain_architecture(report)
            
            # Save explanation to file
            arch_path = os.path.join(os.path.dirname(report_path), f"{report.repository_name.lower().replace(' ', '_')}_architecture.md")
            with open(arch_path, "w") as f:
                f.write(explanation)
                
            print(f"\n===== Architecture Explanation =====\n")
            print(explanation)
            print(f"\nArchitecture explanation saved to: {arch_path}")
    
    except Exception as e:
        print(f"Error analyzing repository: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 