#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze security aspects of the PepperPy codebase.

This script identifies potential security issues specific to AI applications, including:
- Credential management
- Input sanitization
- Prompt injection vulnerabilities
- Data privacy issues
- Model security considerations
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Security patterns to search for
SECURITY_PATTERNS = {
    "hardcoded_api_key": {
        "pattern": r'(api_key|API_KEY|ApiKey|api-key)\s*=\s*["\']([A-Za-z0-9_-]{10,})["\']',
        "description": "Hardcoded API key",
        "severity": "HIGH",
    },
    "hardcoded_secret": {
        "pattern": r'(secret|SECRET|Secret)\s*=\s*["\']([A-Za-z0-9_-]{8,})["\']',
        "description": "Hardcoded secret",
        "severity": "HIGH",
    },
    "password_hardcoded": {
        "pattern": r'(password|PASSWORD|passwd|PASSWD)\s*=\s*["\']([^"\']{4,})["\']',
        "description": "Hardcoded password",
        "severity": "HIGH",
    },
    "unsanitized_prompt": {
        "pattern": r"\.generate\([^)]*user_input",
        "description": "Potentially unsanitized user input in prompt",
        "severity": "MEDIUM",
    },
    "insecure_direct_model_call": {
        "pattern": r"(openai\.Completion\.create|openai\.ChatCompletion\.create)\(",
        "description": "Direct model call without validation",
        "severity": "MEDIUM",
    },
    "debug_mode": {
        "pattern": r"(debug|DEBUG)\s*=\s*True",
        "description": "Debug mode enabled",
        "severity": "LOW",
    },
    "insecure_file_operation": {
        "pattern": r"(open|file)\([^)]*user",
        "description": "Insecure file operation with user input",
        "severity": "HIGH",
    },
    "eval_usage": {
        "pattern": r"eval\(",
        "description": "Use of eval() function",
        "severity": "HIGH",
    },
    "missing_input_validation": {
        "pattern": r"def\s+\w+\([^)]*request[^)]*\):(?![^:]*validate)",
        "description": "Function accepting request without validation",
        "severity": "MEDIUM",
    },
    "plaintext_logging": {
        "pattern": r"log[ging]*\.(info|debug|error|warning)\([^)]*password",
        "description": "Logging sensitive information",
        "severity": "MEDIUM",
    },
}

# AI-specific security checks
AI_SPECIFIC_PATTERNS = {
    "prompt_injection": {
        "pattern": r"\.generate\(.*\)",
        "description": "Potential prompt injection vulnerability",
        "severity": "HIGH",
    },
    "model_validation": {
        "pattern": r"load_model\([^)]*\)",
        "description": "Model loading without validation",
        "severity": "MEDIUM",
    },
    "default_temperature": {
        "pattern": r"temperature\s*=\s*(0\.9|1\.0)",
        "description": "High temperature setting (less deterministic)",
        "severity": "LOW",
    },
    "no_content_filtering": {
        "pattern": r"content_filter\s*=\s*(None|False)",
        "description": "Content filtering disabled",
        "severity": "HIGH",
    },
    "insecure_vector_storage": {
        "pattern": r"(vectorize|embedding|vector_store|vectordb)",
        "description": "Check vector storage security",
        "severity": "INFO",
    },
}

# Recommended mitigations
MITIGATIONS = {
    "hardcoded_api_key": "Use environment variables or a secure secret management system instead of hardcoding API keys.",
    "hardcoded_secret": "Use environment variables or a secure secret management system instead of hardcoding secrets.",
    "password_hardcoded": "Use environment variables or a secure secret management system instead of hardcoding passwords.",
    "unsanitized_prompt": "Implement input validation and sanitization for all user inputs before using them in prompts.",
    "insecure_direct_model_call": "Implement middleware for validation and sanitization of inputs/outputs from LLM calls.",
    "debug_mode": "Ensure debug mode is disabled in production environments.",
    "insecure_file_operation": "Validate and sanitize user inputs before using them in file operations.",
    "eval_usage": "Avoid using eval() as it can lead to code injection. Use safer alternatives.",
    "missing_input_validation": "Implement input validation for all request parameters.",
    "plaintext_logging": "Avoid logging sensitive information or ensure it is properly masked.",
    "prompt_injection": "Implement prompt validation, sanitization, and consider using templates with parameterization.",
    "model_validation": "Validate models before loading, check checksums and sources.",
    "default_temperature": "Consider using lower temperature settings for more deterministic outputs in critical applications.",
    "no_content_filtering": "Enable content filtering for user-facing AI applications.",
    "insecure_vector_storage": "Ensure vector databases are secured, authenticated, and contain no sensitive information.",
}


def find_security_issues(file_path: str) -> List[Dict[str, Any]]:
    """
    Find security issues in a file based on predefined patterns.

    Args:
        file_path: Path to the file to analyze

    Returns:
        List of found security issues
    """
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()

        # Check for general security patterns
        for issue_type, config in {**SECURITY_PATTERNS, **AI_SPECIFIC_PATTERNS}.items():
            pattern = config["pattern"]
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_no = content.count("\n", 0, match.start()) + 1
                line_content = lines[line_no - 1] if line_no <= len(lines) else ""

                # Add context lines
                context_start = max(0, line_no - 3)
                context_end = min(len(lines), line_no + 2)
                context = lines[context_start:context_end]

                issues.append({
                    "file": file_path,
                    "line": line_no,
                    "type": issue_type,
                    "description": config["description"],
                    "severity": config["severity"],
                    "content": line_content.strip(),
                    "context": context,
                    "mitigation": MITIGATIONS.get(
                        issue_type, "Review and address this security concern."
                    ),
                })

        # Look for sensitive file handling patterns in AI context
        if any(
            term in str(Path(file_path))
            for term in ["document", "loader", "embedding", "vector"]
        ):
            with open(file_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    if "open(" in line or "read(" in line:
                        issues.append({
                            "file": file_path,
                            "line": line_no,
                            "type": "ai_data_handling",
                            "description": "File operations in AI data processing",
                            "severity": "INFO",
                            "content": line.strip(),
                            "context": [],
                            "mitigation": "Ensure file operations validate inputs and handle sensitive data appropriately.",
                        })

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return issues


def analyze_security(root_dir: str) -> Dict[str, Any]:
    """
    Analyze the codebase for security issues.

    Args:
        root_dir: Root directory of the codebase

    Returns:
        Dict containing security analysis results
    """
    results = {
        "issues": [],
        "summary": {
            "total_issues": 0,
            "severity_counts": defaultdict(int),
            "type_counts": defaultdict(int),
            "files_with_issues": set(),
        },
    }

    # Find all Python files
    python_files = []
    for root, _, files in os.walk(root_dir):
        # Skip hidden directories and __pycache__
        if (
            any(part.startswith(".") for part in Path(root).parts)
            or "__pycache__" in root
        ):
            continue

        # Skip directories that aren't part of the package
        if "pepperpy" not in root:
            continue

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    # Analyze each file
    for file_path in python_files:
        issues = find_security_issues(file_path)

        if issues:
            results["issues"].extend(issues)
            results["summary"]["files_with_issues"].add(file_path)

            for issue in issues:
                results["summary"]["severity_counts"][issue["severity"]] += 1
                results["summary"]["type_counts"][issue["type"]] += 1

    # Update summary
    results["summary"]["total_issues"] = len(results["issues"])
    results["summary"]["files_with_issues"] = list(
        results["summary"]["files_with_issues"]
    )

    return results


def ai_security_assessment(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform an AI-specific security assessment.

    Args:
        results: Security analysis results

    Returns:
        Dict containing AI security assessment
    """
    assessment = {
        "prompt_injection_risk": "LOW",
        "data_leakage_risk": "LOW",
        "model_security_risk": "LOW",
        "overall_risk": "LOW",
        "recommendations": [],
    }

    # Assess prompt injection risk
    prompt_injection_issues = [
        issue
        for issue in results["issues"]
        if issue["type"] in ["prompt_injection", "unsanitized_prompt"]
    ]

    if len(prompt_injection_issues) > 5:
        assessment["prompt_injection_risk"] = "HIGH"
        assessment["recommendations"].append(
            "Implement comprehensive prompt sanitization and validation throughout the codebase."
        )
    elif len(prompt_injection_issues) > 0:
        assessment["prompt_injection_risk"] = "MEDIUM"
        assessment["recommendations"].append(
            "Address identified prompt injection vulnerabilities and establish consistent patterns."
        )

    # Assess data leakage risk
    data_leakage_issues = [
        issue
        for issue in results["issues"]
        if issue["type"]
        in ["insecure_vector_storage", "plaintext_logging", "insecure_file_operation"]
    ]

    if len(data_leakage_issues) > 5:
        assessment["data_leakage_risk"] = "HIGH"
        assessment["recommendations"].append(
            "Implement a comprehensive data handling policy and review all data storage mechanisms."
        )
    elif len(data_leakage_issues) > 0:
        assessment["data_leakage_risk"] = "MEDIUM"
        assessment["recommendations"].append(
            "Review data handling practices and implement proper sanitization and encryption."
        )

    # Assess model security risk
    model_security_issues = [
        issue
        for issue in results["issues"]
        if issue["type"]
        in ["model_validation", "no_content_filtering", "default_temperature"]
    ]

    if len(model_security_issues) > 5:
        assessment["model_security_risk"] = "HIGH"
        assessment["recommendations"].append(
            "Implement model validation, content filtering, and appropriate parameter settings."
        )
    elif len(model_security_issues) > 0:
        assessment["model_security_risk"] = "MEDIUM"
        assessment["recommendations"].append(
            "Address model security concerns by implementing consistent validation and filtering."
        )

    # Assess overall risk
    risk_levels = [
        assessment["prompt_injection_risk"],
        assessment["data_leakage_risk"],
        assessment["model_security_risk"],
    ]

    if "HIGH" in risk_levels:
        assessment["overall_risk"] = "HIGH"
    elif "MEDIUM" in risk_levels:
        assessment["overall_risk"] = "MEDIUM"

    # Add common recommendations
    assessment["recommendations"].extend([
        "Implement a security review process for AI components",
        "Develop AI-specific security guidelines for developers",
        "Establish monitoring for unusual AI behavior or outputs",
        "Consider implementing rate limiting for AI interactions",
        "Add logging and auditing for AI model inputs and outputs",
    ])

    return assessment


def generate_report(results: Dict[str, Any], assessment: Dict[str, Any]) -> str:
    """
    Generate a markdown report from security analysis results.

    Args:
        results: Security analysis results
        assessment: AI security assessment

    Returns:
        Markdown report
    """
    report = [
        "# PepperPy Security Analysis Report",
        "",
        "## Summary",
        "",
        f"- **Total Issues Found**: {results['summary']['total_issues']}",
        f"- **Files With Issues**: {len(results['summary']['files_with_issues'])}",
        f"- **Overall AI Security Risk**: {assessment['overall_risk']}",
        "",
        "## Severity Breakdown",
        "",
    ]

    # Add severity breakdown
    for severity, count in sorted(
        results["summary"]["severity_counts"].items(),
        key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}.get(x[0], 4),
    ):
        report.append(f"- **{severity}**: {count}")

    report.extend([
        "",
        "## AI Security Assessment",
        "",
        f"- **Prompt Injection Risk**: {assessment['prompt_injection_risk']}",
        f"- **Data Leakage Risk**: {assessment['data_leakage_risk']}",
        f"- **Model Security Risk**: {assessment['model_security_risk']}",
        "",
        "### Recommendations",
        "",
    ])

    # Add recommendations
    for i, recommendation in enumerate(assessment["recommendations"], 1):
        report.append(f"{i}. {recommendation}")

    # Add top issues by severity
    report.extend([
        "",
        "## Top Issues by Severity",
        "",
    ])

    # Group issues by severity
    issues_by_severity = defaultdict(list)
    for issue in results["issues"]:
        issues_by_severity[issue["severity"]].append(issue)

    # Display top issues for each severity
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if severity in issues_by_severity:
            report.extend([
                f"### {severity} Severity Issues",
                "",
            ])

            # Sort by type for grouping
            issues_by_severity[severity].sort(key=lambda x: x["type"])

            # Group by type
            for issue_type, issues in groupby(
                issues_by_severity[severity], key=lambda x: x["type"]
            ):
                issues_list = list(issues)
                report.extend([
                    f"#### {issue_type.replace('_', ' ').title()} ({len(issues_list)})",
                    "",
                    f"*{MITIGATIONS.get(issue_type, 'Review and address this security concern.')}*",
                    "",
                    "Examples:",
                    "",
                ])

                # Show at most 3 examples per type
                for issue in issues_list[:3]:
                    rel_path = os.path.relpath(issue["file"], project_root)
                    report.extend([
                        f"- **{rel_path}:{issue['line']}**:",
                        "  ```python",
                        f"  {issue['content']}",
                        "  ```",
                        "",
                    ])

    # Add detailed issue list (limited to 30)
    report.extend([
        "## Detailed Issue List",
        "",
        "| File | Line | Type | Severity | Description |",
        "|------|------|------|----------|-------------|",
    ])

    # Sort issues by severity and file
    sorted_issues = sorted(
        results["issues"],
        key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}.get(x["severity"], 4),
            x["file"],
            x["line"],
        ),
    )

    for issue in sorted_issues[:30]:
        rel_path = os.path.relpath(issue["file"], project_root)
        report.append(
            f"| {rel_path} | {issue['line']} | {issue['type']} | {issue['severity']} | {issue['description']} |"
        )

    if len(sorted_issues) > 30:
        report.append(f"\n*...and {len(sorted_issues) - 30} more issues*")

    return "\n".join(report)


def groupby(iterable, key=None):
    """
    Simple implementation of itertools.groupby.

    Args:
        iterable: Iterable to group
        key: Function to extract a key from each element

    Returns:
        Generator yielding (key, sub-iterable) pairs
    """
    if key is None:
        key = lambda x: x

    groups = defaultdict(list)
    for item in iterable:
        groups[key(item)].append(item)

    for k, group in groups.items():
        yield k, group


def main():
    """Main function to analyze the codebase and generate a report."""
    print("Analyzing PepperPy codebase for security issues...")
    results = analyze_security(os.path.join(project_root, "pepperpy"))

    # Generate AI security assessment
    assessment = ai_security_assessment(results)

    # Generate report
    report = generate_report(results, assessment)

    # Save report
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, "security_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save raw results for further analysis
    results_path = os.path.join(reports_dir, "security_data.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "results": {
                    "issues": results["issues"],
                    "summary": {
                        k: v
                        for k, v in results["summary"].items()
                        if k != "files_with_issues"
                    },
                    "files_count": len(results["summary"]["files_with_issues"]),
                },
                "assessment": assessment,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"Analysis complete. Report saved to {report_path}")
    print(f"Raw data saved to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
